from typing import List, Dict, Optional

class ResumeRanker:
    def __init__(self, top_n: Optional[int] = None, descending: bool = True):
        """
        top_n: how many top results to return (None for all)
        descending: True to rank from highest to lowest match%
        """
        self.top_n = top_n
        self.descending = descending

    def rank(self, resumes: List[Dict]) -> List[Dict]:
        """
        Rank resumes by match_percent and return top N if specified.
        Assumes contact info (email, phone) is already flattened.
        """
        ranked = sorted(
            resumes,
            key=lambda x: x.get("match_percent", 0),
            reverse=self.descending
        )

        top_ranked = ranked[:self.top_n] if self.top_n is not None else ranked

        for res in top_ranked:
            # Title case the name
            if "name" in res:
                res["name"] = res["name"].title()

            # Round match_percent
            if "match_percent" in res and isinstance(res["match_percent"], (int, float)):
                res["match_percent"] = round(res["match_percent"], 2)

            # Do NOT reassign email or phone — they are already present
            # This is the fix — don't wipe out contact info

        return top_ranked


    def print_ranked(self, ranked_resumes: List[Dict]):
        """
        Print a readable view of ranked resumes with breakdown.
        """
        for idx, res in enumerate(ranked_resumes, 1):
            name = res.get("name", "Unknown")
            email = res.get("email", "N/A")
            phone = res.get("phone", "N/A")
            print(f"Rank {idx}: {name} - {res.get('match_percent', 0):.2f}%")
            print(f"  Skills: {res.get('skills_score', 0)}% | Experience: {res.get('experience_score', 0)}% | Education: {res.get('education_score', 0)}% | Projects: {res.get('project_score', 0)}%")
            print(f"  Domain Alignment: {res.get('domain_match_score', 0)}%")
            print(f"  Contact: 📧 {email} | 📞 {phone}")
            print(f"  Missing Skills: {', '.join(res.get('missing_skills', [])) or 'None'}")
            print("-" * 50)
