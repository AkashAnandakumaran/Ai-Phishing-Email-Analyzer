import os
import argparse
from email import policy
from email.parser import BytesParser
from rich.console import Console
from rich.table import Table
import openai

console = Console()

# Rule-based phishing detection
def detect_phishing_rules(text):
    indicators = {
        "urgent": "Uses urgent language",
        "click here": "Contains 'click here'",
        "password": "Mentions password",
        "verify": "Requests verification",
        "bank": "Mentions bank/financial info",
        "login": "Mentions login"
    }
    found = []
    text_lower = text.lower()
    for keyword, reason in indicators.items():
        if keyword in text_lower:
            found.append(reason)
    score = len(found) * 20
    level = "High" if score >= 60 else "Medium" if score >= 30 else "Low"
    return score, level, found

# AI explanation (optional)
def ai_explanation(email_text):
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("GPT_MODEL", "gpt-4o-mini")
    if not api_key:
        return "No API key set. Skipping AI explanation."
    openai.api_key = api_key
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a cybersecurity analyst. Explain why this email may be phishing."},
                {"role": "user", "content": email_text}
            ]
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"AI explanation failed: {e}"

def parse_eml(path):
    with open(path, 'rb') as f:
        msg = BytesParser(policy=policy.default).parse(f)
    return msg.get_body(preferencelist=('plain')).get_content()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phishing Email Analyzer")
    parser.add_argument("file", help="Path to .eml file")
    parser.add_argument("--ai", action="store_true", help="Enable AI explanation")
    parser.add_argument("--report", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--out", help="Save report to file")
    args = parser.parse_args()

    email_text = parse_eml(args.file)
    score, level, reasons = detect_phishing_rules(email_text)

    if args.report == "markdown":
        report = f"# Phishing Analysis Report\n\n**Risk Score:** {score}\n**Risk Level:** {level}\n\n## Reasons:\n"
        report += "\n".join(f"- {r}" for r in reasons) if reasons else "No major phishing indicators found."
        if args.ai:
            report += "\n\n## AI Explanation:\n" + ai_explanation(email_text)
    else:
        import json
        report = json.dumps({
            "score": score,
            "level": level,
            "reasons": reasons,
            "ai_explanation": ai_explanation(email_text) if args.ai else None
        }, indent=2)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(report)
        console.print(f"[green]Report saved to {args.out}[/green]")
    else:
        console.print(report)
