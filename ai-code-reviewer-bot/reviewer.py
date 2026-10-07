import sys

class CodeReviewer:
    def review_code(self, code_snippet: str) -> dict:
        issues = []
        if "eval(" in code_snippet:
            issues.append({"level": "CRITICAL", "message": "Avoid using eval() due to security risks."})
        if "except:" in code_snippet:
            issues.append({"level": "WARNING", "message": "Bare except clause detected. Specify exception type."})
            
        return {
            "total_issues": len(issues),
            "status": "PASSED" if len(issues) == 0 else "NEEDS_REVISION",
            "issues": issues
        }

if __name__ == "__main__":
    reviewer = CodeReviewer()
    code = "try:\n    eval(user_input)\nexcept:\n    pass"
    report = reviewer.review_code(code)
    print(report)