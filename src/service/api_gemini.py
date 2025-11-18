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
            questionnaire_answers: JSON string berisi jawaban kuisioner
            file_content: Konten file pendukung dalam bytes
            file_name: Nama file pendukung
            
        Returns:
            Dict berisi analysis, score, dan recommendations
        """
        try:
            # Parse jawaban kuisioner
            answers = json.loads(questionnaire_answers)
            
            # Buat prompt untuk analisis
            prompt = self._create_analysis_prompt(answers)
            
            # Tambahkan informasi file jika ada
            if file_content and file_name:
                file_info = self._process_supporting_file(file_content, file_name)
                prompt += f"\n\nSUPPORTING FILE INFORMATION:\n{file_info}"
            
            try:
                # Coba kirim ke Gemini AI
                print(f"[DEBUG] Sending prompt to Gemini AI...")
                print(f"[DEBUG] Model: {self.model}")
                response = self.model.generate_content(prompt)
                result_text = getattr(response, "text", str(response))
                print(f"[DEBUG] Gemini AI Response received: {result_text[:100]}...")
                
                # Parse hasil analisis
                return self._parse_analysis_result(result_text)
                
            except Exception as api_error:
                # Fallback ke analisis sederhana jika API error
                print(f"[DEBUG] Gemini API Error: {str(api_error)}")
                print("[DEBUG] Falling back to simplified analysis...")
                return self._generate_fallback_analysis(answers, file_name)
            
        except json.JSONDecodeError:
            raise ValueError("Format jawaban kuisioner tidak valid (bukan JSON)")
        except Exception as e:
            raise Exception(f"Error dalam analisis: {str(e)}")
    

    def _create_analysis_prompt(self, answers: Dict) -> str:
        prompt = f"""
You are an experienced mining systems evaluation expert. Your task is to analyze mining evaluation system questionnaire answers and provide a comprehensive assessment.

QUESTIONNAIRE ANSWERS:
{json.dumps(answers, indent=2, ensure_ascii=False)}

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
    "score": [score 1-100 based on overall evaluation],
    "recommendations": ["recommendation 1", "recommendation 2", "recommendation 3"]
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
        
        # Generate relevant recommendations
        recommendations = self._generate_recommendations_based_on_data(answers)
        
        return {
            "analysis": analysis,
            "score": score,
            "recommendations": recommendations
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

RECOMMENDATIONS FOCUS:
Key areas for enhancement include safety protocol optimization, environmental impact monitoring, and operational efficiency improvements.

Note: This analysis was generated using fallback system due to API limitations. For detailed AI-powered analysis, please try again later.
""".strip()
        
        return analysis
    
    def _generate_recommendations_based_on_data(self, answers: Dict) -> List[str]:
        """Generate recommendations based on data analysis."""
        flattened = self._flatten_dict(answers)
        recommendations = []
        
        # Safety recommendations
        if any('safety' in key.lower() for key in flattened.keys()):
            recommendations.append("Enhance safety protocols and monitoring systems")
        
        # Environmental recommendations
        if any('environment' in key.lower() for key in flattened.keys()):
            recommendations.append("Strengthen environmental impact mitigation strategies")
        
        # Operational recommendations
        if any('operational' in key.lower() or 'efficiency' in key.lower() for key in flattened.keys()):
            recommendations.append("Optimize operational efficiency and resource utilization")
        
        # Management recommendations
        if any('management' in key.lower() or 'workforce' in key.lower() for key in flattened.keys()):
            recommendations.append("Develop comprehensive workforce management programs")
        
        # Default recommendations if none specific
        if not recommendations:
            recommendations = [
                "Implement comprehensive monitoring systems",
                "Enhance regulatory compliance procedures",
                "Develop continuous improvement strategies"
            ]
        
        return recommendations[:4]  # Limit to 4 recommendations
    
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
            json_pattern = r'\{[^{}]*"analysis"[^{}]*"score"[^{}]*"recommendations"[^{}]*\}'
            matches = re.findall(json_pattern, result_text, re.DOTALL)
            
            if matches:
                return json.loads(matches[0])
            
            # Fallback: buat struktur manual
            return {
                "analysis": result_text[:500] + ".." if len(result_text) > 500 else result_text,
                "score": 75,  # Default score
                "recommendations": ["Lakukan review lebih lanjut", "Konsultasi dengan ahli", "Update dokumentasi"]
            }
            
        except Exception:
            return {
                "analysis": "Analisis berhasil dilakukan namun format respons tidak standar. " + result_text[:300],
                "score": 70,
                "recommendations": ["Review hasil analisis", "Validasi dengan expert", "Lakukan assessment ulang"]
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
