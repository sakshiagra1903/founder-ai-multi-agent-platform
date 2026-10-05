from typing import List, Optional, Dict, Any


def _get_recommendation(score: float) -> str:
    """Map score to hiring recommendation."""
    if score >= 85:
        return "Strong Hire"
    elif score >= 70:
        return "Hire"
    elif score >= 55:
        return "Consider"
    else:
        return "Reject"


class ScoringService:
    """Ranks, filters, and assigns hiring recommendations."""

    def filter_and_rank(
        self,
        candidates: List[Dict[str, Any]],
        min_experience: Optional[float] = None,
        required_skills: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Filter candidates by criteria.
        Apply soft penalties for missing required skills.
        Assign hiring recommendations.
        Rank from highest to lowest score.
        """
        filtered = []

        for c in candidates:
            score = c.get("overall_score", c.get("score", 0))

            # Hard filter: minimum experience
            if min_experience and c.get("experience_years", 0) < min_experience:
                continue

            # Soft penalty: missing required skills
            if required_skills:
                cand_skills_lower = [s.lower() for s in c.get("skills", [])]
                missing_from_resume = [
                    sk for sk in required_skills
                    if sk.lower() not in cand_skills_lower
                ]
                
                # Only penalize skills truly missing (not already in missing_skills)
                truly_missing = [
                    m for m in missing_from_resume
                    if m.lower() not in [ms.lower() for ms in c.get("missing_skills", [])]
                ]
                
                # Update missing skills list
                c["missing_skills"] = list(set(c.get("missing_skills", []) + truly_missing))
                
                # Apply penalty: -8 points per missing skill
                score = max(0.0, score - 8 * len(truly_missing))

            c["overall_score"] = round(score, 1)
            c["score"] = round(score, 1)
            c["hiring_recommendation"] = _get_recommendation(score)
            filtered.append(c)

        # Sort by score descending
        filtered.sort(key=lambda x: x["overall_score"], reverse=True)

        # Assign ranks (1, 2, 3, ...)
        for i, c in enumerate(filtered):
            c["rank"] = i + 1

        return filtered

    def build_final_ranking(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build the final ranking table rows."""
        return [
            {
                "rank": c["rank"],
                "name": c.get("name") or "Unknown",
                "overall_score": c["overall_score"],
                "hiring_recommendation": c["hiring_recommendation"],
            }
            for c in candidates
        ]

    def pick_best(self, candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Select the best candidate and explain why."""
        if not candidates:
            return {}
        
        best = candidates[0]
        name = best.get("name") or "Unknown"
        
        # Use AI-generated reason if available, otherwise fall back
        reason = best.get("recommendation_reason") or best.get("match_reason") or ""
        
        if not reason:
            score = best["overall_score"]
            if score >= 85:
                reason = f"{name} is an exceptional fit with a score of {score}/100. Strong across all dimensions."
            elif score >= 70:
                reason = f"{name} is a solid hire with a score of {score}/100. Good match for the role."
            else:
                reason = f"{name} scored highest at {score}/100 among candidates reviewed."
        
        return {
            "name": name,
            "reason": reason,
        }


scoring_service = ScoringService()
