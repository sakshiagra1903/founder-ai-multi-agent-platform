import re
from typing import Dict, Any, List

# Common skills keyword bank
SKILL_KEYWORDS = [
    "python", "javascript", "typescript", "java", "c++", "c#", "go", "rust", "ruby", "php",
    "react", "next.js", "vue", "angular", "node.js", "fastapi", "django", "flask", "spring",
    "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "docker", "kubernetes", "aws", "gcp", "azure", "terraform",
    "machine learning", "deep learning", "nlp", "computer vision", "pytorch", "tensorflow",
    "langchain", "openai", "llm", "rag",
    "sql", "nosql", "rest", "graphql", "grpc",
    "git", "ci/cd", "agile", "scrum",
    "pandas", "numpy", "scikit-learn", "data analysis", "power bi", "tableau",
]


class ParsingService:
    """Extracts structured fields from raw resume text."""

    def parse(self, text: str) -> Dict[str, Any]:
        return {
            "name": self._extract_name(text),
            "skills": self._extract_skills(text),
            "experience_years": self._extract_experience(text),
            "education": self._extract_education(text),
        }

    def _extract_name(self, text: str) -> str:
        """Heuristic: first non-empty line that looks like a name."""
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        for line in lines[:5]:
            # A name: 2-4 words, each capitalized, no numbers
            words = line.split()
            if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words if w) and not any(c.isdigit() for c in line):
                return line
        return lines[0] if lines else "Unknown"

    def _extract_skills(self, text: str) -> List[str]:
        lower = text.lower()
        found = [skill for skill in SKILL_KEYWORDS if skill in lower]
        # Deduplicate preserving order
        seen = set()
        result = []
        for s in found:
            if s not in seen:
                seen.add(s)
                result.append(s)
        return result

    def _extract_experience(self, text: str) -> float:
        """Look for patterns like '3 years', '5+ years', '2 yrs'."""
        patterns = [
            r"(\d+)\+?\s*years?\s+of\s+experience",
            r"(\d+)\+?\s*years?\s+experience",
            r"(\d+)\+?\s*yrs?\s+experience",
            r"experience\s+of\s+(\d+)\+?\s*years?",
        ]
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return float(match.group(1))
        return 0.0

    def _extract_education(self, text: str) -> List[str]:
        degrees = ["phd", "ph.d", "doctorate", "master", "msc", "mba", "bachelor", "bsc", "b.tech", "b.e", "b.s", "associate"]
        lower = text.lower()
        lines = text.splitlines()
        found = []
        for line in lines:
            if any(deg in line.lower() for deg in degrees):
                clean = line.strip()
                if clean and len(clean) < 200:
                    found.append(clean)
        return found[:3]


parsing_service = ParsingService()
