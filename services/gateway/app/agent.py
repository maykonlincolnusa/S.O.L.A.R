from __future__ import annotations

import os
from collections import Counter
from typing import Any

import httpx

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")


def summarize_context(timeline: list[dict[str, Any]], alerts: list[dict[str, Any]]) -> dict[str, Any]:
    source_counter = Counter(event.get("source_type", "unknown") for event in timeline)
    open_alerts = [alert for alert in alerts if alert.get("status") == "open"]
    high_alerts = [alert for alert in open_alerts if alert.get("priority") == "high"]
    with_geo = [event for event in timeline if event.get("latitude") is not None and event.get("longitude") is not None]
    avg_severity = (
        round(sum(int(event.get("severity", 1)) for event in timeline) / max(len(timeline), 1), 2)
        if timeline
        else 0.0
    )

    return {
        "event_count": len(timeline),
        "open_alert_count": len(open_alerts),
        "high_alert_count": len(high_alerts),
        "avg_severity": avg_severity,
        "geolocated_events": len(with_geo),
        "top_sources": source_counter.most_common(3),
    }


async def answer_question(
    question: str,
    timeline: list[dict[str, Any]],
    alerts: list[dict[str, Any]],
) -> dict[str, Any]:
    context = summarize_context(timeline, alerts)

    if OPENAI_API_KEY:
        prompt = (
            "You are a tactical intelligence copilot for SOLAR. "
            "Provide short and actionable answers. "
            f"Question: {question}\n"
            f"Context: {context}\n"
            "Include one operational recommendation."
        )
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/responses",
                    headers={
                        "Authorization": f"Bearer {OPENAI_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": OPENAI_MODEL,
                        "input": prompt,
                        "temperature": 0.2,
                    },
                )
                response.raise_for_status()
                body = response.json()
                text = body.get("output_text")
                if not text:
                    outputs = body.get("output", [])
                    texts = []
                    for block in outputs:
                        for item in block.get("content", []):
                            if item.get("type") == "output_text":
                                texts.append(item.get("text", ""))
                    text = "\n".join(texts).strip()
                if text:
                    return {
                        "answer": text,
                        "source": "openai",
                        "confidence": 0.82,
                        "insights": [
                            f"Recent events: {context['event_count']}",
                            f"Open alerts: {context['open_alert_count']}",
                        ],
                    }
        except Exception:
            pass

    return heuristic_answer(question=question, context=context)


def heuristic_answer(question: str, context: dict[str, Any]) -> dict[str, Any]:
    q = question.lower()
    top_sources_text = ", ".join([f"{name} ({count})" for name, count in context["top_sources"]]) or "no sources"

    if "risk" in q:
        answer = (
            f"Current risk is moderate: {context['high_alert_count']} high-priority alerts out of "
            f"{context['open_alert_count']} open alerts."
        )
    elif "anomaly" in q:
        answer = (
            f"There are {context['open_alert_count']} active alerts. "
            "Prioritize validation of anomaly cases with severity above 4."
        )
    elif "machine learning" in q or "ml" in q or "deep learning" in q:
        answer = (
            "The platform runs three risk engines: rule-based analytics, ML logistic regression, "
            "and a deep MLP model. Use model comparison to reduce single-model bias."
        )
    elif "source" in q or "origin" in q:
        answer = f"Top data sources by volume right now: {top_sources_text}."
    else:
        answer = (
            f"Operational summary: {context['event_count']} recent events, "
            f"average severity {context['avg_severity']}, "
            f"{context['open_alert_count']} open alerts."
        )

    return {
        "answer": answer,
        "source": "heuristic",
        "confidence": 0.65,
        "insights": [
            f"Top sources: {top_sources_text}",
            f"Geolocated events: {context['geolocated_events']}",
            "Recommendation: run predictive evaluation every 5 minutes.",
        ],
    }
