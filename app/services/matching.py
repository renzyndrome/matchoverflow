import json
import os
import logging
from typing import List, Dict, Tuple, Any
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import openai

from ..models.user import User, Interest, LookingForEnum
from ..models.schemas import MatchResult, UserProfile

load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

class MatchingService:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            openai.api_key = api_key
            self.has_openai = True
            logger.info("✅ OpenAI API key configured successfully")
        else:
            self.has_openai = False
            logger.warning("⚠️ No OpenAI API key found - will use fallback matching algorithm")
    
    def calculate_match_percentage(self, user1: User, user2: User) -> Tuple[int, List[str], List[str]]:
        """Calculate match percentage between two users using AI if available"""
        # Get common interests
        user1_interests = set(i.name for i in user1.interests)
        user2_interests = set(i.name for i in user2.interests)
        common_interests = list(user1_interests.intersection(user2_interests))
        
        # Check if looking_for preferences are compatible
        if not self._check_looking_for_compatibility(user1.looking_for, user2.looking_for):
            return 0, common_interests, ["Incompatible relationship preferences"]
        
        # Try to use AI for matching if available
        if self.has_openai and (user1.match_preference or user2.match_preference):
            try:
                ai_result = self._get_ai_compatibility_analysis(user1, user2)
                
                # Ensure score is between 0 and 100
                score = max(0, min(100, ai_result.get("score", 50)))
                reasons = ai_result.get("reasons", ["Based on profile analysis"])
                
                # Add common interests to reasons if any
                if common_interests:
                    reasons.append(f"Share interests: {', '.join(common_interests[:3])}")
                
                return score, common_interests, reasons
                
            except Exception as e:
                logger.error(f"Error in AI matching: {e}")
                # Fall back to simple matching
                return self._simple_match_calculation(user1, user2, common_interests)
        else:
            # Use simple matching algorithm
            return self._simple_match_calculation(user1, user2, common_interests)
    
    def _check_looking_for_compatibility(self, user1_looking: LookingForEnum, user2_looking: LookingForEnum) -> bool:
        """Check if two users' looking_for preferences are compatible"""
        # If either is looking for "both", they're compatible
        if user1_looking == LookingForEnum.both or user2_looking == LookingForEnum.both:
            return True
        
        # Otherwise, they must be looking for the same thing
        return user1_looking == user2_looking
    
    def _simple_match_calculation(self, user1: User, user2: User, common_interests: List[str]) -> Tuple[int, List[str], List[str]]:
        """Simple fallback matching algorithm"""
        base_score = 30  # Lower base score
        
        # Give major points if both have match preferences
        preference_score = 0
        if user1.match_preference and user2.match_preference:
            # If both have preferences, assume some compatibility
            preference_score = 40
        elif user1.match_preference or user2.match_preference:
            # If only one has preferences, lower score
            preference_score = 20
        
        # Add points for common interests
        interest_score = min(len(common_interests) * 5, 20)
        
        # Add points for age proximity
        age_score = 0
        if user1.age and user2.age:
            age_diff = abs(user1.age - user2.age)
            if age_diff <= 2:
                age_score = 10
            elif age_diff <= 5:
                age_score = 5
        
        total_score = min(base_score + preference_score + interest_score + age_score, 100)
        
        reasons = []
        if user1.match_preference and user2.match_preference:
            reasons.append("Both have detailed preferences")
        if common_interests:
            reasons.append(f"You share {len(common_interests)} common interests")
        if age_score > 0:
            reasons.append("Similar age group")
        if user1.looking_for == user2.looking_for:
            reasons.append(f"Both looking for {user1.looking_for}")
        
        return total_score, common_interests, reasons
    
    def find_matches(self, user: User, db: Session, min_match_percentage: int = 80) -> List[MatchResult]:
        """Find compatible matches for a user"""
        # Get all potential matches
        potential_matches = db.query(User).filter(
            User.id != user.id,
            User.is_active == True
        ).all()
        
        matches = []
        
        for potential_match in potential_matches:
            # Skip if already picked
            existing_pick = any(pick.picked_id == potential_match.id for pick in user.picks_made)
            if existing_pick:
                continue
            
            # Skip if looking for incompatible types
            if not self._check_looking_for_compatibility(user.looking_for, potential_match.looking_for):
                continue
            
            # Calculate match percentage
            match_percentage, common_interests, compatibility_reasons = self.calculate_match_percentage(
                user, potential_match
            )
            
            if match_percentage >= min_match_percentage:
                # Create a UserProfile with properly parsed traits
                user_profile = UserProfile(
                    id=potential_match.id,
                    username=potential_match.username,
                    full_name=potential_match.full_name,
                    bio=potential_match.bio,
                    age=potential_match.age,
                    looking_for=potential_match.looking_for,
                    is_active=potential_match.is_active,
                    created_at=potential_match.created_at,
                    interests=potential_match.interests,
                    match_preference=potential_match.match_preference,
                    traits=json.loads(potential_match.traits) if potential_match.traits else []
                )
                
                matches.append(MatchResult(
                    user=user_profile,
                    match_percentage=match_percentage,
                    common_interests=common_interests,
                    compatibility_reasons=compatibility_reasons
                ))
        
        # Sort by match percentage
        matches.sort(key=lambda x: x.match_percentage, reverse=True)
        
        return matches 

    def _get_ai_compatibility_analysis(self, user1: User, user2: User) -> Dict[str, Any]:
        """Use OpenAI to analyze compatibility between two users"""
        if not self.has_openai:
            logger.warning("⚠️ OpenAI not available, skipping AI analysis")
            return {"score": 50, "reasons": ["Based on shared interests"]}
        
        try:
            logger.info(f"🤖 Requesting AI compatibility analysis for {user1.username} and {user2.username}")
            
            # Prepare user profiles for analysis
            user1_profile = {
                "bio": user1.bio or "No bio provided",
                "interests": [i.name for i in user1.interests],
                "looking_for": user1.looking_for,
                "match_preference": user1.match_preference or "No preference specified",
                "traits": json.loads(user1.traits) if user1.traits else []
            }
            
            user2_profile = {
                "bio": user2.bio or "No bio provided",
                "interests": [i.name for i in user2.interests],
                "looking_for": user2.looking_for,
                "match_preference": user2.match_preference or "No preference specified",
                "traits": json.loads(user2.traits) if user2.traits else []
            }
            
            prompt = f"""Analyze the compatibility between these two users for a student matching platform.
            
{user1.username}'s Profile:
- Bio: {user1_profile['bio']}
- Interests: {', '.join(user1_profile['interests'])}
- Looking for: {user1_profile['looking_for']}
- Ideal match: {user1_profile['match_preference']}
- Traits: {', '.join(user1_profile['traits'])}

{user2.username}'s Profile:
- Bio: {user2_profile['bio']}
- Interests: {', '.join(user2_profile['interests'])}
- Looking for: {user2_profile['looking_for']}
- Ideal match: {user2_profile['match_preference']}
- Traits: {', '.join(user2_profile['traits'])}

Provide a compatibility score from 0-100 and 2-3 specific reasons why they match well.
Focus heavily on whether each user matches what the other is looking for in their match_preference.
When writing the reasons, use their actual names ({user1.username} and {user2.username}) instead of generic terms.
Return as JSON: {{"score": number, "reasons": ["reason1", "reason2", "reason3"]}}"""

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a matchmaking expert analyzing compatibility between students."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=200
            )
            
            tokens_used = response.get('usage', {}).get('total_tokens', 0)
            logger.info(f"✅ OpenAI API call successful - tokens used: {tokens_used}")
            
            result = json.loads(response.choices[0].message.content)
            logger.info(f"🎯 AI compatibility score: {result['score']}%")
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse AI response as JSON: {e}")
            return {"score": 50, "reasons": ["Based on profile compatibility"]}
        except Exception as e:
            logger.error(f"❌ OpenAI API error: {type(e).__name__}: {str(e)}")
            return {"score": 50, "reasons": ["Based on profile compatibility"]} 