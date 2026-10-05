"""promptfoo provider: runs the real Agent.generate pipeline on this machine.

Each step (model calls, man page excerpt, checks) is sent as an OpenTelemetry
span to promptfoo's receiver, under the test's trace, so `promptfoo view`
shows what happened behind each command.
"""

import functools
import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

import thetaterm.agent as agent_module
from thetaterm.agent import Agent
from thetaterm.cli import DEFAULT_BASE_URL, DEFAULT_MODEL

# Simple, not batch: the worker can be stopped before a batch flushes
_provider = TracerProvider(resource=Resource.create({"service.name": "thetaterm"}))
_provider.add_span_processor(
    SimpleSpanProcessor(OTLPSpanExporter("http://127.0.0.1:4318/v1/traces"))
)
tracer = _provider.get_tracer("thetaterm.evals")
MAX_ATTR = 20000


def traced(name, attrs):
    """Wrap fn in a span; attrs(args, kwargs, result) -> span attributes."""

    def wrap(fn):
        @functools.wraps(fn)
        def inner(*args, **kwargs):
            with tracer.start_as_current_span(name) as span:
                result = fn(*args, **kwargs)
                for k, v in attrs(args, kwargs, result).items():
                    span.set_attribute(k, str(v)[:MAX_ATTR])
                return result

        return inner

    return wrap


Agent.ask = traced(
    "ask",
    lambda a, kw, r: {
        "gen_ai.request.model": a[0].model,
        "prompt": a[1],
        "reply": r,
    },
)(Agent.ask)
Agent.choose = traced("choose", lambda a, kw, r: {"chosen": r})(Agent.choose)
# generate() looks these up in the module at call time
agent_module.reference = traced(
    "reference", lambda a, kw, r: {"command": a[0], "chars": len(r), "reference": r}
)(agent_module.reference)
agent_module.problem = traced(
    "problem", lambda a, kw, r: {"command": a[0], "problem": r or "none"}
)(agent_module.problem)


def call_api(prompt, options, context):
    model = options.get("config", {}).get("model") or os.getenv(
        "THETATERM_MODEL", DEFAULT_MODEL
    )
    base_url = os.getenv("THETATERM_BASE_URL") or DEFAULT_BASE_URL
    parent = TraceContextTextMapPropagator().extract(
        {"traceparent": (context or {}).get("traceparent", "")}
    )
    with tracer.start_as_current_span("generate", context=parent) as span:
        span.set_attribute("gen_ai.request.model", model)
        span.set_attribute("query", prompt)
        thinking = bool(options.get("config", {}).get("thinking"))
        span.set_attribute("thinking", thinking)
        agent = Agent(model, base_url, os.getenv("THETATERM_API_KEY"), thinking)
        try:
            command = agent.generate(prompt)
        except RuntimeError as e:
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            return {"error": str(e)}
        span.set_attribute("command", command)
        return {"output": command}
