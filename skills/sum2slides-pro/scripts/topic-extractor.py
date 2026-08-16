#!/usr/bin/env python3
"""
Sum2Slides Pro — Topic Extractor
Analyze parsed conversation to extract topics, decisions, action items,
consensus points, divergences, and timeline.
"""

import argparse
import json
import re
import sys
from pathlib import Path


DECISION_PATTERNS = [
    r'(同意|好|就这么定|ok|agreed|sounds good|deal|就这样|confirm|approved)',
    r'(确定|决定|定下来|decided|decision|conclusion)',
    r'(按这个来|就这么办|go with|let\'s do it|let\'s go)',
]

ACTION_PATTERNS = [
    r'(负责|来做|协调|安排|assign|owner|负责方|todo|action|跟进)',
    r'(周五前|下周|明天|by\s+\w+|deadline|due|截止)',
    r'(出方案|出计划|prepare|draft|write up|整理|提交)',
]

CONSENSUS_PATTERNS = [
    r'\b(同意|赞同|赞成|支持)\b',
    r'^(好的?|行|可以|没问题|ok\b|deal\b)',
    r'(就这么定|就这么办|按这个来|就这个方向)',
    r'(方向对|思路好|方案可行|看起来不错|值得一试)',
]

DIVERGENCE_PATTERNS = [
    r'(但是|但|不过|可是|然而)',
    r'(不同意|不太认同|持保留意见|保留看法)',
    r'(担心|顾虑|隐忧|隐患|问题在于|风险在于)',
    r'(另一种思路|换个角度|另一方面|不过话说回来)',
    r'(不太确定|不确定|存疑|有待商榷|有待验证)',
    r'(方向对[^。]*但|思路[^。]*不过|同意[^。]*但是)',
]


def extract_topics(messages, min_size=3):
    """Segment messages into topics by theme shifts and markers."""
    topics = []
    current_topic = None
    current_msgs = []

    for msg in messages:
        if msg.get("type") == "topic_marker":
            if current_topic and current_msgs:
                topics.append({"topic": current_topic, "messages": current_msgs})
            current_topic = msg.get("topic", "Untitled")
            current_msgs = []
        elif msg.get("topic"):
            if current_topic and current_topic != msg["topic"]:
                if current_msgs:
                    topics.append({"topic": current_topic, "messages": current_msgs})
                current_topic = msg["topic"]
                current_msgs = [msg]
            else:
                current_topic = msg["topic"]
                current_msgs.append(msg)
        elif "speaker" in msg:
            current_msgs.append(msg)

    if current_topic and current_msgs:
        topics.append({"topic": current_topic, "messages": current_msgs})

    # Merge small topics into previous
    merged = []
    for t in topics:
        if merged and len(t["messages"]) < min_size:
            merged[-1]["messages"].extend(t["messages"])
            merged[-1]["topic"] += f" / {t['topic']}"
        else:
            merged.append(t)

    return merged if merged else [{"topic": "General Discussion", "messages": messages}]


def extract_decisions(messages):
    """Detect decision points from agreement patterns."""
    decisions = []
    for i, msg in enumerate(messages):
        if "speaker" not in msg:
            continue
        text = msg.get("text", "")
        for pattern in DECISION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                context = ""
                if i > 0 and "speaker" in messages[i - 1]:
                    context = messages[i - 1].get("text", "")[:100]
                decisions.append({
                    "decision": text[:150],
                    "by": msg.get("speaker", ""),
                    "context_snippet": context[:100],
                    "message_index": i
                })
                break
    return decisions


def extract_action_items(messages):
    """Extract action items with assignee and deadline."""
    items = []
    for i, msg in enumerate(messages):
        if "speaker" not in msg:
            continue
        text = msg.get("text", "")
        for pattern in ACTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                lines = text.split('\n')
                for line in lines:
                    assignee = msg.get("speaker", "")
                    items.append({
                        "task": line.strip()[:200],
                        "assignee": assignee,
                        "mentioned_by": assignee,
                        "message_index": i
                    })
                break

    seen = set()
    unique_items = []
    for item in items:
        key = item["task"][:50]
        if key not in seen:
            seen.add(key)
            unique_items.append(item)
    return unique_items


def extract_consensus(messages):
    """Extract points of consensus: explicit agreement from participants."""
    consensus = []
    for i, msg in enumerate(messages):
        if "speaker" not in msg:
            continue
        text = msg.get("text", "")
        for pattern in CONSENSUS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                # What are they agreeing to? Check previous message context
                context_before = ""
                context_author = ""
                for j in range(i - 1, max(i - 4, -1), -1):
                    if j >= 0 and "speaker" in messages[j]:
                        context_before = messages[j].get("text", "")[:150]
                        context_author = messages[j].get("speaker", "")
                        break

                consensus.append({
                    "agreement": text[:150],
                    "agreed_by": msg.get("speaker", ""),
                    "responding_to": context_before,
                    "respondent_speaker": context_author,
                    "message_index": i
                })
                break
    return consensus


def extract_divergence(messages):
    """Extract points of divergence: differing opinions, concerns, alternatives."""
    divergence = []
    for i, msg in enumerate(messages):
        if "speaker" not in msg:
            continue
        text = msg.get("text", "")
        for pattern in DIVERGENCE_PATTERNS:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                divergence.append({
                    "viewpoint": text[:200],
                    "raised_by": msg.get("speaker", ""),
                    "trigger_word": m.group(0)[:20],
                    "message_index": i
                })
                break
    return divergence


def extract_timeline(messages):
    """Build chronological sequence of key moments."""
    timeline = []
    for i, msg in enumerate(messages):
        if "speaker" not in msg:
            continue
        text = msg.get("text", "")
        if len(text) > 60 or any(w in text for w in ["关键", "重要", "核心", "concern", "risk", "opportunity"]):
            timeline.append({
                "index": i,
                "speaker": msg.get("speaker", ""),
                "snippet": text[:120]
            })
    return timeline


def analyze(filepath, min_topic_size=3, output_path=None):
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    if "error" in data:
        return data

    messages = data.get("messages", [])
    chat_messages = [m for m in messages if "speaker" in m]

    topics = extract_topics(messages, min_topic_size)
    decisions = extract_decisions(chat_messages)
    actions = extract_action_items(chat_messages)
    consensus = extract_consensus(chat_messages)
    divergence = extract_divergence(chat_messages)
    timeline = extract_timeline(chat_messages)

    # Per-topic analysis
    topic_analysis = []
    for t in topics:
        topic_msgs = t["messages"]
        topic_texts = [m.get("text", "") for m in topic_msgs if "speaker" in m]

        # Filter global results to this topic
        topic_decisions = [d for d in decisions
                          if any(txt and d.get("context_snippet", "") and
                                 txt[:100] == d.get("context_snippet", "")
                                 for txt in topic_texts)]
        topic_actions = [a for a in actions
                        if any(txt and a.get("task", "") and
                               txt[:200] == a.get("task", "")
                               for txt in topic_texts)]

        topic_consensus = [c for c in consensus
                          if any(c.get("agreement", "") in txt for txt in topic_texts)]
        topic_divergence = [d for d in divergence
                          if any(d.get("viewpoint", "") in txt for txt in topic_texts)]

        topic_analysis.append({
            "title": t["topic"],
            "message_count": len(topic_msgs),
            "speakers": list(set(m.get("speaker", "") for m in topic_msgs if "speaker" in m)),
            "decisions": topic_decisions[:3],
            "action_items": topic_actions[:5],
            "consensus": topic_consensus[:3],
            "divergence": topic_divergence[:3],
            "key_points": [
                m.get("text", "")[:150] for m in topic_msgs
                if "speaker" in m and len(m.get("text", "")) > 40
            ][:5]
        })

    result = {
        "metadata": {
            "total_messages": data.get("total_messages", len(chat_messages)),
            "speakers": data.get("speakers", []),
            "topics_found": len(topics),
            "decisions_found": len(decisions),
            "action_items_found": len(actions),
            "consensus_found": len(consensus),
            "divergence_found": len(divergence)
        },
        "topics": topic_analysis,
        "decisions": decisions[:10],
        "action_items": actions[:10],
        "consensus": consensus[:10],
        "divergence": divergence[:10],
        "timeline": timeline[:10]
    }

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(
            json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    return result


def main():
    parser = argparse.ArgumentParser(description="Sum2Slides Pro — Topic Extractor")
    parser.add_argument("--input", required=True, help="Parsed conversation JSON")
    parser.add_argument("--min-topic-size", type=int, default=3,
                        help="Min messages per topic")
    parser.add_argument("--output", help="Output outline JSON path")
    args = parser.parse_args()

    result = analyze(args.input, args.min_topic_size, args.output)

    m = result["metadata"]
    print(f"Topics: {m['topics_found']} | "
          f"Decisions: {m['decisions_found']} | "
          f"Actions: {m['action_items_found']} | "
          f"Consensus: {m['consensus_found']} | "
          f"Divergence: {m['divergence_found']}")

    if args.output:
        print(f"Outline saved: {args.output}")
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
