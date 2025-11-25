import os
import json
from typing import Dict, List, Optional
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class GeminiAnalyzer:
    def __init__(self):
        self.api_key = os.getenv('API_GEMINI')
        print(f"[DEBUG] API Key loaded: {'Yes' if self.api_key else 'No'}")
        print(f"[DEBUG] API Key starts with: {self.api_key[:10] if self.api_key else 'None'}...")
        
        if not self.api_key or self.api_key == 'your_api_key_here':
            raise ValueError('API_GEMINI not configured. Get key from: https://makersuite.google.com/app/apikey')
        
        try:
            # Configure API key
            genai.configure(api_key=self.api_key)
            # Initialize model dengan API yang benar
            self.model = genai.GenerativeModel(model_name="gemini-2.5-flash")
            print("[Real Mode] GeminiAnalyzer initialized with gemini-2.5-flash")
        except Exception as e:
            print(f"[DEBUG] Error configuring Gemini: {e}")
            raise

    def ask(self, prompt: str, model_name: str = "gemini-2.5-flash") -> str:
        """Send a prompt to the Gemini model and return the text response."""
        try:
            model = genai.GenerativeModel(model_name=model_name)
            response = model.generate_content(prompt)
            return getattr(response, "text", repr(response))
        except Exception as e:
            # Fallback to mock response if API fails
            print(f"Gemini API Error: {str(e)}")
            return self._generate_fallback_response(prompt)

    async def analyze_mining_evaluation(self, questionnaire_answers: str, file_content: Optional[bytes] = None, file_name: Optional[str] = None) -> Dict:
        """Analisis jawaban kuisioner mining evaluation system menggunakan Gemini AI dengan fallback.
        
        Args:
            questionnaire_answers: String berisi jawaban kuisioner (bisa plain text atau JSON)
            file_content: Konten file pendukung dalam bytes
            file_name: Nama file pendukung
            
        Returns:
            Dict berisi analysis, score, dan detail scoring.
        """
        try:
            # Parse jawaban kuisioner - coba JSON dulu, kalau gagal treat sebagai string biasa
            answers = None
            is_json = False
            try:
                answers = json.loads(questionnaire_answers)
                is_json = True
            except json.JSONDecodeError:
                # Jika bukan JSON, treat sebagai plain text string
                answers = {"raw_text": questionnaire_answers}
                is_json = False
            
            # Check if this is ESG scoring format (has 'questions' with 'answer' field)
            is_esg_format = False
            if is_json and isinstance(answers, dict):
                questions = answers.get('questions', [])
                if questions and all(isinstance(q, dict) and 'answer' in q for q in questions):
                    is_esg_format = True
            
            # Calculate score based on format
            calculated_score = None
            if is_esg_format:
                print(f"[DEBUG] Detected ESG scoring format")
                calculated_score = self._calculate_esg_score(answers)
            elif is_json and isinstance(answers, dict):
                print(f"[DEBUG] Using weighted scoring format")
                calculated_score = self._calculate_weighted_score(answers)
            
            # Jika ada file content, proses juga
            file_info = None
            if file_content and file_name:
                file_info = self._process_supporting_file(file_content, file_name)
            
            # Jika ESG format dan sudah ada scoring, langsung return
            if is_esg_format and calculated_score:
                print(f"[DEBUG] Returning ESG score: {calculated_score['score']}")
                return calculated_score
            
            # Buat prompt untuk analisis Gemini (untuk non-ESG format)
            prompt = self._create_analysis_prompt(answers, is_json)
            
            if file_info:
                prompt += f"\n\nSUPPORTING FILE INFORMATION:\n{file_info}"
            
            try:
                # Coba kirim ke Gemini AI
                print(f"[DEBUG] Sending prompt to Gemini AI...")
                response = self.model.generate_content(prompt)
                result_text = getattr(response, "text", str(response))
                print(f"[DEBUG] Gemini AI Response received: {result_text[:100]}...")
                
                # Parse hasil analisis
                result = self._parse_analysis_result(result_text)
                
                # Override score jika sudah dihitung
                if calculated_score is not None:
                    result['score'] = calculated_score['score']
                    result['score_details'] = calculated_score.get('score_details')
                
                return result
                
            except Exception as api_error:
                # Fallback ke analisis sederhana jika API error
                print(f"[DEBUG] Gemini API Error: {str(api_error)}")
                print("[DEBUG] Falling back to simplified analysis...")
                result = self._generate_fallback_analysis(answers, file_name)
                
                # Tambahkan calculated score jika ada
                if calculated_score is not None:
                    result['score'] = calculated_score['score']
                    result['score_details'] = calculated_score.get('score_details')
                
                return result
            
        except Exception as e:
            raise Exception(f"Error dalam analisis: {str(e)}")
    

    def _create_analysis_prompt(self, answers: Dict, is_json: bool = True) -> str:
        # Format questionnaire info sesuai dengan tipe input
        if is_json:
            answers_text = f"QUESTIONNAIRE ANSWERS (JSON):\n{json.dumps(answers, indent=2, ensure_ascii=False)}"
        else:
            answers_text = f"QUESTIONNAIRE ANSWERS (Plain Text):\n{answers.get('raw_text', '')}"
        
        prompt = f"""
You are an experienced mining systems evaluation expert. Your task is to analyze mining evaluation system questionnaire answers and provide a comprehensive assessment.

{answers_text}

Please conduct an in-depth analysis using the following criteria:

1. TECHNICAL EVALUATION:
   - Completeness of mining methodology
   - Compliance with industry standards
   - Safety and environmental aspects
   - Operational efficiency

2. MANAGEMENT EVALUATION:
   - Planning and strategy
   - Resource management
   - Monitoring and control systems
   - Compliance and regulations

3. SUSTAINABILITY ASPECTS:
   - Environmental impact
   - Social responsibility
   - Economic sustainability
   - Technological innovation

Provide the results in JSON format with the following structure:
{{
    "analysis": "comprehensive analysis in English (maximum 500 words)",
    "score": [score 1-100 based on overall evaluation]
}}

Ensure the analysis is objective, constructive, and provides useful insights for mining system improvements.
"""
        return prompt
    
    def _generate_fallback_response(self, prompt: str) -> str:
        """Generate fallback response when API fails."""
        return "API quota exceeded. Using fallback analysis system."
    
    def _generate_fallback_analysis(self, answers: Dict, file_name: Optional[str] = None) -> Dict:
        """Generate fallback analysis when Gemini API is unavailable."""
        # Simple scoring based on data completeness
        score = self._calculate_simple_score(answers)
        
        # Generate basic analysis
        analysis = self._create_basic_analysis(answers, file_name, score)
        
        return {
            "analysis": analysis,
            "score": score
        }
    
    def _calculate_simple_score(self, answers: Dict) -> int:
        """Calculate score based on data quality and completeness."""
        base_score = 70
        
        # Key areas we expect to see
        key_areas = ['safety', 'environment', 'operational', 'management', 'compliance', 'financial']
        coverage_bonus = 0
        
        for area in key_areas:
            if any(area.lower() in str(key).lower() or area.lower() in str(value).lower() 
                   for key, value in self._flatten_dict(answers).items()):
                coverage_bonus += 3
        
        # Data completeness bonus
        completeness_bonus = min(len(self._flatten_dict(answers)) * 2, 20)
        
        # Quality indicators
        quality_bonus = 0
        flattened = self._flatten_dict(answers)
        
        # Look for specific quality indicators
        for key, value in flattened.items():
            if isinstance(value, (int, float)) and value > 0:
                quality_bonus += 1
            elif isinstance(value, str):
                if any(word in value.lower() for word in ['excellent', 'good', 'high', 'advanced', 'comprehensive']):
                    quality_bonus += 2
                elif any(word in value.lower() for word in ['poor', 'low', 'inadequate', 'minimal']):
                    quality_bonus -= 1
        
        final_score = base_score + coverage_bonus + completeness_bonus + quality_bonus
        return max(60, min(95, final_score))
    
    def _calculate_esg_score(self, answers: Dict) -> Dict:
        """
        ESG Scoring dengan strict rules:
        - Answer A=0%, B=25%, C=50%, D=75%, E=100%
        - earned_points = max_points × percentage
        - JANGAN reduce score ke 0 kecuali jawaban A atau bukti 100% kontradiksi
        - final_score = (sum earned_points / total max_points) × 100
        
        Input format:
        {
            "questions": [
                {
                    "id": "q1",
                    "question": "Mine closure planning...",
                    "max_points": 20,
                    "answer": "D",  # A, B, C, D, or E
                    "evidence": "Optional evidence text"
                },
                ...
            ]
        }
        
        Returns:
            Dict with Analysis and Score
        """
        try:
            questions = answers.get('questions', [])
            
            if not questions:
                return None
            
            # Answer percentage mapping
            answer_mapping = {
                'A': 0,
                'B': 0.25,
                'C': 0.50,
                'D': 0.75,
                'E': 1.00
            }
            
            question_details = []
            total_earned_points = 0
            total_max_points = 0
            analysis_parts = []
            
            strengths = []
            risks = []
            
            for idx, question in enumerate(questions):
                try:
                    q_id = question.get('id', f'q{idx+1}')
                    q_text = question.get('question', '')
                    max_points = float(question.get('max_points', 100))
                    answer = str(question.get('answer', 'A')).upper()
                    evidence = question.get('evidence', '')
                    
                    # Validate answer
                    if answer not in answer_mapping:
                        print(f"[DEBUG] Invalid answer '{answer}' for {q_id}, defaulting to A")
                        answer = 'A'
                    
                    percentage = answer_mapping[answer]
                    earned_points = max_points * percentage
                    
                    # Check for contradiction (strict rule: only reduce if evidence 100% contradicts)
                    final_earned_points = earned_points
                    contradiction_found = False
                    
                    if evidence:
                        contradiction_keywords = ['not implemented', 'no evidence', 'absent', 'none', 'not found', 'tidak ada']
                        if any(keyword.lower() in evidence.lower() for keyword in contradiction_keywords):
                            if answer not in ['A']:  # Only override if answer suggests some level
                                print(f"[DEBUG] Potential contradiction found in {q_id}, but keeping score as evidence may be incomplete")
                                contradiction_found = True
                    
                    total_earned_points += final_earned_points
                    total_max_points += max_points
                    
                    # Categorize for analysis
                    if percentage >= 0.75:
                        strengths.append(f"• {q_id}: {q_text[:60]}... ({answer} - {percentage*100:.0f}%)")
                    elif percentage < 0.50:
                        risk_note = " [Evidence contradiction noted]" if contradiction_found else ""
                        risks.append(f"• {q_id}: {q_text[:60]}... ({answer} - {percentage*100:.0f}%){risk_note}")
                    
                    question_details.append({
                        'id': q_id,
                        'answer': answer,
                        'percentage': percentage,
                        'max_points': max_points,
                        'earned_points': final_earned_points,
                        'contradiction_risk': contradiction_found
                    })
                    
                except (ValueError, TypeError) as e:
                    print(f"[DEBUG] Error parsing question {idx+1}: {str(e)}")
                    continue
            
            # Calculate final score
            if total_max_points > 0:
                final_score = (total_earned_points / total_max_points) * 100
            else:
                final_score = 0
            
            # Build analysis narrative
            analysis_text = f"""ESG SUSTAINABILITY EVALUATION - RAIMES MINING QUESTIONNAIRE

SCORING METHODOLOGY:
- Percentage values: A=0%, B=25%, C=50%, D=75%, E=100%
- Earned points = Max points × Percentage
- Final score = (Total earned points / Total max points) × 100

ASSESSMENT SUMMARY:
Total Questions: {len(question_details)}
Total Points Available: {total_max_points}
Total Points Earned: {round(total_earned_points, 2)}
Final Score: {round(final_score, 2)}%

"""
            
            if strengths:
                analysis_text += f"STRENGTHS (D–E Rating):\n" + "\n".join(strengths) + "\n\n"
            
            if risks:
                analysis_text += f"AREAS FOR IMPROVEMENT (≤C Rating):\n" + "\n".join(risks) + "\n\n"
            
            analysis_text += """KEY FOCUS AREAS FOR MINING SUSTAINABILITY:
• Mine Closure & Restoration Planning
• Free Prior Informed Consent (FPIC) with Indigenous Communities
• ESG Supplier Compliance & Chain of Custody
• Long-term Environmental & Social Sustainability
• Transparent Governance & Stakeholder Engagement
"""
            
            return {
                "analysis": analysis_text,
                "score": round(final_score, 2),
                "score_details": {
                    "total_questions": len(question_details),
                    "total_max_points": total_max_points,
                    "total_earned_points": round(total_earned_points, 2),
                    "final_score_percentage": round(final_score, 2),
                    "question_details": question_details
                }
            }
            
        except Exception as e:
            print(f"[DEBUG] Error in _calculate_esg_score: {str(e)}")
            return None

    def _calculate_weighted_score(self, answers: Dict) -> Dict:
        """
        Hitung score berdasarkan weighted system:
        Score setiap soal = max_score * weight_percentage
        Total max score = 10000
        Final score = (total_weighted_score / 10000) * 100
        
        Struktur input yang diharapkan:
        {
            "questions": [
                {
                    "id": "q1",
                    "max_score": 100,
                    "weight": 0.75,  # atau "75%" atau 75
                    "answer": "yes"
                },
                ...
            ]
        }
        
        Returns:
            Dict dengan detail scoring breakdown
        """
        try:
            questions = answers.get('questions', [])
            
            if not questions:
                # Jika tidak ada struktur questions, return None
                return None
            
            question_scores = []
            total_weighted_score = 0
            total_max_possible = 0
            
            for idx, question in enumerate(questions):
                try:
                    # Parse max_score
                    max_score = float(question.get('max_score', 100))
                    
                    # Parse weight - bisa dalam format 0.75, "75%", atau 75
                    weight_raw = question.get('weight', 1.0)
                    if isinstance(weight_raw, str):
                        if '%' in weight_raw:
                            weight = float(weight_raw.replace('%', '')) / 100
                        else:
                            weight = float(weight_raw) / 100 if float(weight_raw) > 1 else float(weight_raw)
                    else:
                        weight = float(weight_raw) / 100 if weight_raw > 1 else float(weight_raw)
                    
                    # Ensure weight is between 0 and 1
                    weight = max(0, min(1, weight))
                    
                    # Hitung score untuk soal ini
                    question_score = max_score * weight
                    total_weighted_score += question_score
                    total_max_possible += max_score
                    
                    question_scores.append({
                        "question_id": question.get('id', f'q{idx+1}'),
                        "max_score": max_score,
                        "weight": weight,
                        "weight_percentage": f"{weight * 100:.1f}%",
                        "score_obtained": question_score,
                        "answer": question.get('answer', '')
                    })
                    
                except (ValueError, TypeError) as e:
                    print(f"[DEBUG] Error parsing question {idx+1}: {str(e)}")
                    continue
            
            # Hitung final score
            # Total max score jika 100% adalah 10000
            # Jadi final score = (total_weighted_score / total_max_possible) * 10000 / 100
            if total_max_possible > 0:
                percentage = (total_weighted_score / total_max_possible) * 100
            else:
                percentage = 0
            
            final_score = int((total_weighted_score / total_max_possible * 100)) if total_max_possible > 0 else 0
            
            return {
                "total_questions": len(question_scores),
                "total_weighted_score": round(total_weighted_score, 2),
                "total_max_possible": round(total_max_possible, 2),
                "percentage": round(percentage, 2),
                "final_score": min(100, max(0, final_score)),  # Clamp between 0-100
                "question_details": question_scores,
                "scoring_method": "Weighted scoring: each question score = max_score × weight"
            }
            
        except Exception as e:
            print(f"[DEBUG] Error in _calculate_weighted_score: {str(e)}")
            return None
    
    def _flatten_dict(self, d: Dict, parent_key: str = '', sep: str = '_') -> Dict:
        """Flatten nested dictionary."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    def _create_basic_analysis(self, answers: Dict, file_name: Optional[str], score: int) -> str:
        """Create basic analysis based on available data."""
        num_responses = len(self._flatten_dict(answers))
        file_note = f" and supporting file '{file_name}'" if file_name else ""
        
        if score >= 85:
            performance = "demonstrates excellent performance"
        elif score >= 75:
            performance = "shows good performance with room for improvement"
        elif score >= 65:
            performance = "indicates satisfactory performance requiring attention"
        else:
            performance = "reveals areas needing significant improvement"
        
        analysis = f"""
Based on the mining evaluation questionnaire with {num_responses} data points{file_note}, the system {performance}.

TECHNICAL ASSESSMENT:
The evaluation covers multiple operational areas. Data completeness suggests a structured approach to mining operations management.

COMPLIANCE & MANAGEMENT:
The provided information indicates awareness of regulatory and operational requirements. Management systems appear to be documented.

Note: This analysis was generated using fallback system due to API limitations. For detailed AI-powered analysis, please try again later.
""".strip()
        
        return analysis
    
    def _process_supporting_file(self, file_content: bytes, file_name: str) -> str:
        try:
            if file_name.lower().endswith(('.txt', '.csv', '.json')):
                return f"File: {file_name}\nKonten:\n{file_content.decode('utf-8', errors='ignore')}"
            
            file_size = len(file_content)
            return f"File: {file_name}\nUkuran: {file_size} bytes\nTipe: File pendukung (konten tidak dapat dibaca langsung)"
            
        except Exception as e:
            return f"File: {file_name}\nError reading file: {str(e)}"
    
    def _parse_analysis_result(self, result_text: str) -> Dict:
        """Parse hasil analisis dari respons Gemini."""
        try:
            # Coba parse sebagai JSON
            if result_text.strip().startswith('{'):
                return json.loads(result_text)
            
            # Jika bukan JSON, cari pola JSON dalam teks
            import re
            json_pattern = r'\{[^{}]*"analysis"[^{}]*"score"[^{}]*\}'
            matches = re.findall(json_pattern, result_text, re.DOTALL)
            
            if matches:
                return json.loads(matches[0])
            
            # Fallback: buat struktur manual
            return {
                "analysis": result_text[:500] + ".." if len(result_text) > 500 else result_text,
                "score": 75  # Default score
            }
            
        except Exception:
            return {
                "analysis": "Analisis berhasil dilakukan namun format respons tidak standar. " + result_text[:300],
                "score": 70
            }

analyzer = GeminiAnalyzer()

async def analyze_mining_questionnaire(questionnaire_answers: str, supporting_file_content: Optional[bytes] = None, supporting_file_name: Optional[str] = None) -> Dict:
    return await analyzer.analyze_mining_evaluation(
        questionnaire_answers=questionnaire_answers,
        file_content=supporting_file_content,
        file_name=supporting_file_name
    )

# Legacy functions untuk backward compatibility
def ask(prompt: str, model_name: str = "gemini-2.5-flash") -> str:
    """Legacy ask function untuk backward compatibility."""
    return analyzer.ask(prompt, model_name)

def main():
        import argparse

        parser = argparse.ArgumentParser(description="Gemini CLI — ask the model a question")
        parser.add_argument("-p", "--prompt", help="One-shot prompt to send and exit")
        parser.add_argument("-m", "--model", default="gemini-2.5-flash", help="Model name to use")
        args = parser.parse_args()

        if args.prompt:
            try:
                print(ask(args.prompt, args.model))
            except Exception as e:
                print("Error calling Gemini:", e)
            return

        print("Gemini CLI — interactive mode. Type 'exit' or 'quit' to leave.")
        try:
            while True:
                try:
                    prompt = input("> ")
                except EOFError:
                    print()
                    break
                if prompt is None:
                    break
                prompt = prompt.strip()
                if not prompt:
                    continue
                if prompt.lower() in ("exit", "quit"):
                    break
                try:
                    answer = ask(prompt, args.model)
                    print("\n", answer, "\n")
                except Exception as e:
                    print("Error calling Gemini:", e)
        except KeyboardInterrupt:
            print("\nExiting.")
