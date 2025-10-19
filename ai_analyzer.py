"""
AI Analyzer module for AI Market Insight Bot.
Uses Google Gemini API to analyze news and provide trader-specific insights.
"""

import logging
from config import GEMINI_API_KEY

logger = logging.getLogger(__name__)


class AIAnalyzer:
    """Analyzes news using Google Gemini API."""

    def __init__(self):
        """Initialize AI analyzer."""
        self.api_key = GEMINI_API_KEY
        self.client = None

        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                # ✅ FIX: Use gemini-2.0-flash-exp (experimental but available)
                # Stable alternatives: gemini-2.5-flash, gemini-2.0-flash
                self.client = genai.GenerativeModel('gemini-2.0-flash-exp')
                logger.info("Google Gemini client initialized successfully (gemini-2.0-flash-exp)")
            except Exception as e:
                logger.warning(f"Failed to initialize Google Gemini client: {e}")
    
    def analyze(self, headline, summary):
        """
        Analyze news (wrapper method for compatibility).

        Args:
            headline: Article headline
            summary: Article summary/description

        Returns:
            Dict with trader insights and sentiment
        """
        return self.analyze_with_gpt(headline, summary)

    def analyze_with_gpt(self, headline, summary):
        """
        Analyze news using Google Gemini API.

        Args:
            headline: Article headline
            summary: Article summary/description

        Returns:
            Dict with trader insights and sentiment
        """
        if not self.client:
            logger.warning("Google Gemini API key not configured. Using fallback analysis.")
            return self._fallback_analysis(headline, summary)

        try:
            prompt = f"""
Analyze the following financial news for different trader types:

Headline: {headline}
Summary: {summary}

Provide analysis in this exact format:
1. Scalper: [2-3 sentence insight for scalpers]
2. Day Trader: [2-3 sentence insight for day traders]
3. Swing Trader: [2-3 sentence insight for swing traders]
4. Investor: [2-3 sentence insight for long-term investors]
5. Sentiment: [Bullish/Bearish/Neutral]

Be concise and actionable.
            """

            response = self.client.generate_content(prompt)
            analysis_text = response.text
            logger.info("Successfully analyzed news with Google Gemini")

            return self._parse_gpt_response(analysis_text)

        except Exception as e:
            logger.error(f"Error calling Google Gemini API: {e}")
            return self._fallback_analysis(headline, summary)
    
    def _parse_gpt_response(self, response_text):
        """Parse GPT response into structured format."""
        try:
            lines = response_text.strip().split("\n")
            
            result = {
                "scalper": "",
                "day_trader": "",
                "swing_trader": "",
                "investor": "",
                "sentiment": "Neutral"
            }
            
            current_key = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if "Scalper:" in line:
                    current_key = "scalper"
                    result["scalper"] = line.split("Scalper:", 1)[1].strip()
                elif "Day Trader:" in line:
                    current_key = "day_trader"
                    result["day_trader"] = line.split("Day Trader:", 1)[1].strip()
                elif "Swing Trader:" in line:
                    current_key = "swing_trader"
                    result["swing_trader"] = line.split("Swing Trader:", 1)[1].strip()
                elif "Investor:" in line:
                    current_key = "investor"
                    result["investor"] = line.split("Investor:", 1)[1].strip()
                elif "Sentiment:" in line:
                    sentiment_text = line.split("Sentiment:", 1)[1].strip()
                    if "Bullish" in sentiment_text:
                        result["sentiment"] = "Bullish"
                    elif "Bearish" in sentiment_text:
                        result["sentiment"] = "Bearish"
                    else:
                        result["sentiment"] = "Neutral"
                elif current_key and line:
                    result[current_key] += " " + line
            
            return result
        
        except Exception as e:
            logger.error(f"Error parsing GPT response: {e}")
            return self._fallback_analysis("", "")
    
    def _fallback_analysis(self, headline, summary):
        """Fallback analysis when OpenAI is not available."""
        logger.info("Using fallback analysis (no OpenAI)")
        
        combined_text = (headline + " " + summary).lower()
        
        # Simple sentiment detection
        bullish_keywords = ["surge", "rally", "bull", "gain", "rise", "jump", "record", "high", "bull run"]
        bearish_keywords = ["crash", "fall", "bear", "loss", "drop", "decline", "down", "low", "sell-off"]
        
        sentiment = "Neutral"
        if any(keyword in combined_text for keyword in bullish_keywords):
            sentiment = "Bullish"
        elif any(keyword in combined_text for keyword in bearish_keywords):
            sentiment = "Bearish"
        
        return {
            "scalper": "Watch for volatility opportunities. Monitor support/resistance levels closely.",
            "day_trader": "Track intraday momentum. Use technical indicators for entry/exit signals.",
            "swing_trader": "Identify trend direction. Hold positions for 2-5 day moves.",
            "investor": "Focus on fundamental impact. Consider long-term portfolio allocation.",
            "sentiment": sentiment
        }

