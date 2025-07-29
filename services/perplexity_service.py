import requests
import json
import re
from typing import Dict, Any, Optional, List
from enum import Enum

class ThreatType(Enum):
    AIRCRAFT = "aircraft"
    SAM_SYSTEM = "sam_system"
    MUNITION = "munition"
    NAVAL = "naval"
    GROUND_SYSTEM = "ground_system"
    UNKNOWN = "unknown"

class PerplexityService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def detect_threat_type(self, threat_name: str) -> ThreatType:
        """Detect the type of threat based on the name and common patterns."""
        threat_lower = threat_name.lower()
        
        # Aircraft patterns
        aircraft_patterns = [
            r'f-\d+', r'mig-\d+', r'su-\d+', r'j-\d+', r'jf-\d+', r'eurofighter',
            r'rafale', r'gripen', r'typhoon', r'lightning', r'raptor', r'eagle',
            r'falcon', r'hornet', r'viper', r'phantom', r'tomcat', r'intruder'
        ]
        
        # SAM/Radar patterns
        sam_patterns = [
            r's-\d+', r'sa-\d+', r'patriot', r'thaad', r'iron dome', r'david\'s sling',
            r'aegis', r'sm-\d+', r'rim-\d+', r'nasams', r'hawk', r'chaparral'
        ]
        
        # Munition patterns
        munition_patterns = [
            r'gbu-\d+', r'agm-\d+', r'aim-\d+', r'amraam', r'sidewinder', r'maverick',
            r'hellfire', r'javelin', r'tow', r'spike', r'brimstone', r'storm shadow',
            r'scalp', r'jdam', r'sdb', r'jassm', r'tomahawk', r'harpoon'
        ]
        
        # Naval patterns
        naval_patterns = [
            r'destroyer', r'frigate', r'cruiser', r'carrier', r'submarine', r'corvette',
            r'class', r'ddg-\d+', r'ffg-\d+', r'ssn-\d+', r'cv-\d+', r'cvn-\d+'
        ]
        
        # Ground system patterns
        ground_patterns = [
            r'himars', r'mlrs', r'caesar', r'pzh', r'paladin', r'archer', r'k9',
            r'bradley', r'abrams', r'leopard', r'challenger', r'merkava', r't-\d+',
            r'm\d+a\d+', r'bmp-\d+', r'btr-\d+'
        ]
        
        # Check patterns
        for pattern in aircraft_patterns:
            if re.search(pattern, threat_lower):
                return ThreatType.AIRCRAFT
        
        for pattern in sam_patterns:
            if re.search(pattern, threat_lower):
                return ThreatType.SAM_SYSTEM
        
        for pattern in munition_patterns:
            if re.search(pattern, threat_lower):
                return ThreatType.MUNITION
        
        for pattern in naval_patterns:
            if re.search(pattern, threat_lower):
                return ThreatType.NAVAL
        
        for pattern in ground_patterns:
            if re.search(pattern, threat_lower):
                return ThreatType.GROUND_SYSTEM
        
        return ThreatType.UNKNOWN
    
    def get_research_prompt(self, threat_name: str, threat_type: ThreatType) -> str:
        """Generate a research prompt based on threat type."""
        
        base_prompt = f"""Research the military threat/system: {threat_name}

Please provide comprehensive, current information including:"""

        if threat_type == ThreatType.AIRCRAFT:
            return base_prompt + """
- Country of origin and development timeline
- Initial operational capability date
- Primary role and mission
- All major variants with key differences
- Performance specifications (speed, range, service ceiling)
- Armament capabilities and weapon systems
- Recent combat deployments or exercises (2020-2025)
- Notable technical features or capabilities
- Export customers and international operations
- Any recent upgrades or modernization programs

Format this as a detailed military threat assessment."""

        elif threat_type == ThreatType.SAM_SYSTEM:
            return base_prompt + """
- Country of origin and development timeline
- Initial operational capability date
- Primary role (air defense, missile defense, etc.)
- System variants and configurations
- Engagement ranges for different target types
- Radar systems and integration capabilities
- Target types it can engage (aircraft, missiles, etc.)
- Recent deployments or combat use (2020-2025)
- Integration with other defense systems
- Export customers and international deployments
- Recent upgrades or modernization programs

Format this as a detailed military threat assessment."""

        elif threat_type == ThreatType.MUNITION:
            return base_prompt + """
- Country of origin and development timeline
- Initial operational capability date
- Primary role and target types
- All variants and their specific capabilities
- Technical specifications (range, warhead, guidance)
- Platform integration (what launches/carries it)
- Recent combat activity and deployments (2020-2025)
- Effectiveness and notable engagements
- Export customers and international use
- Recent upgrades or new variants

Format this as a detailed military threat assessment."""

        elif threat_type == ThreatType.NAVAL:
            return base_prompt + """
- Country of origin and class details
- Initial operational capability date
- Primary role and mission capabilities
- Class variants and ship numbers
- Specifications (displacement, speed, range)
- Armament and sensor systems
- Recent deployments or exercises (2020-2025)
- Notable capabilities or technologies
- Export customers or international cooperation
- Recent upgrades or modernization programs

Format this as a detailed military threat assessment."""

        elif threat_type == ThreatType.GROUND_SYSTEM:
            return base_prompt + """
- Country of origin and development timeline
- Initial operational capability date
- Primary role and capabilities
- System variants and configurations
- Technical specifications (range, mobility, firepower)
- Recent combat deployments or exercises (2020-2025)
- Notable technical features
- Export customers and international use
- Recent upgrades or modernization programs
- Integration with other systems

Format this as a detailed military threat assessment."""

        else:  # UNKNOWN
            return base_prompt + """
- Country of origin and development timeline
- Initial operational capability date
- Primary role and capabilities
- Technical specifications and variants
- Recent activities or deployments (2020-2025)
- Notable features or capabilities
- International use or export

Format this as a detailed military threat assessment."""

    def research_threat(self, threat_name: str) -> Dict[str, Any]:
        """Research a threat using Perplexity AI."""
        try:
            # Detect threat type
            threat_type = self.detect_threat_type(threat_name)
            
            # Generate research prompt
            prompt = self.get_research_prompt(threat_name, threat_type)
            
            # Make API call to Perplexity
            payload = {
                "model": "sonar",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a military analyst providing detailed, factual threat assessments. Focus on current, verified information from reliable defense sources."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 2000,
                "temperature": 0.2,
                "return_citations": True
            }
            
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                research_content = result['choices'][0]['message']['content']
                citations = result.get('citations', [])
                
                return {
                    "success": True,
                    "threat_name": threat_name,
                    "threat_type": threat_type.value,
                    "research_content": research_content,
                    "citations": citations,
                    "raw_response": result
                }
            else:
                return {
                    "success": False,
                    "error": f"API request failed with status {response.status_code}: {response.text}",
                    "threat_name": threat_name,
                    "threat_type": threat_type.value
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Research failed: {str(e)}",
                "threat_name": threat_name,
                "threat_type": "unknown"
            }

    def format_threat_profile(self, research_data: Dict[str, Any]) -> str:
        """Format the research into a standardized threat profile matching newsletter style."""
        if not research_data.get("success"):
            return f"❌ Research failed: {research_data.get('error', 'Unknown error')}"
        
        threat_name = research_data["threat_name"]
        threat_type = research_data["threat_type"]
        content = research_data["research_content"]
        citations = research_data.get("citations", [])
        
        parsed_data = self._parse_research_content(content, threat_type)
        
        # Generate both formats
        newsletter_format = self._format_newsletter_profile(threat_name, threat_type, parsed_data, citations)
        research_format = self._format_research_profile(threat_name, threat_type, parsed_data, citations)
        
        return {
            "newsletter_format": newsletter_format,
            "research_format": research_format
        }
    
    def _parse_research_content(self, content: str, threat_type: str) -> Dict[str, str]:
        """Parse research content to extract key information fields."""
        parsed = {
            "country_of_origin": "Unknown",
            "ioc_date": "Unknown", 
            "primary_role": "Unknown",
            "variants": "Unknown",
            "specifications": "Unknown",
            "recent_activity": "Unknown",
            "notable_features": "Unknown",
            "operators": "Unknown",
            "fun_facts": "Unknown"
        }
        
        # Simple parsing logic to extract key information
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for key information patterns
            if "country of origin" in line.lower() or "developed by" in line.lower():
                parsed["country_of_origin"] = self._extract_value_from_line(line)
            elif "initial operational capability" in line.lower() or "ioc" in line.lower():
                parsed["ioc_date"] = self._extract_value_from_line(line)
            elif "primary role" in line.lower() or "mission" in line.lower():
                parsed["primary_role"] = self._extract_value_from_line(line)
            elif "variant" in line.lower():
                if parsed["variants"] == "Unknown":
                    parsed["variants"] = line
                else:
                    parsed["variants"] += "\n" + line
            elif "speed" in line.lower() or "range" in line.lower() or "specifications" in line.lower():
                if parsed["specifications"] == "Unknown":
                    parsed["specifications"] = line
                else:
                    parsed["specifications"] += "\n" + line
            elif "recent" in line.lower() or any(year in line for year in ["2020", "2021", "2022", "2023", "2024", "2025"]):
                if parsed["recent_activity"] == "Unknown":
                    parsed["recent_activity"] = line
                else:
                    parsed["recent_activity"] += "\n" + line
            elif "export" in line.lower() or "operator" in line.lower() or "customer" in line.lower():
                if parsed["operators"] == "Unknown":
                    parsed["operators"] = line
                else:
                    parsed["operators"] += "\n" + line
        
        return parsed
    
    def _extract_value_from_line(self, line: str) -> str:
        """Extract the value part from a line containing key information."""
        if ":" in line:
            return line.split(":", 1)[1].strip()
        return line.strip()
    
    def _format_aircraft_profile(self, threat_name: str, data: Dict[str, str], citations: List[str]) -> str:
        """Format aircraft threat profile in standardized format."""
        profile = f"""**Threat:** {threat_name}
**Country of Origin:** {data['country_of_origin']}
**Initial Operational Capability:** {data['ioc_date']}
**Primary Role:** {data['primary_role']}

**Variants**
{self._format_section_content(data['variants'])}

**Performance Specifications**
{self._format_section_content(data['specifications'])}

**Recent Combat Activity/Deployments (2020-2025)**
{self._format_section_content(data['recent_activity'])}

**Notable Technical Features**
{self._format_section_content(data['notable_features'])}

**Export Customers and International Operations**
{self._format_section_content(data['operators'])}

**Fun Facts**
{self._format_section_content(data['fun_facts'])}"""
        
        return self._add_citations(profile, citations)
    
    def _format_sam_profile(self, threat_name: str, data: Dict[str, str], citations: List[str]) -> str:
        """Format SAM system threat profile in standardized format."""
        profile = f"""**Threat:** {threat_name}
**Country of Origin:** {data['country_of_origin']}
**Initial Operational Capability:** {data['ioc_date']}
**Primary Role:** {data['primary_role']}

**Variants**
{self._format_section_content(data['variants'])}

**Engagement Range**
{self._format_section_content(data['specifications'])}

**Targets**
{self._format_section_content(data['notable_features'])}

**Recent Combat Activity (2020-2025)**
{self._format_section_content(data['recent_activity'])}

**Export Customers and Deployments**
{self._format_section_content(data['operators'])}

**Fun Facts**
{self._format_section_content(data['fun_facts'])}"""
        
        return self._add_citations(profile, citations)
    
    def _format_munition_profile(self, threat_name: str, data: Dict[str, str], citations: List[str]) -> str:
        """Format munition threat profile in standardized format."""
        profile = f"""**Threat:** {threat_name}
**Country of Origin:** {data['country_of_origin']}
**Initial Operational Capability:** {data['ioc_date']}
**Primary Role:** {data['primary_role']}

**Variants**
{self._format_section_content(data['variants'])}

**Technical Specifications**
{self._format_section_content(data['specifications'])}

**Recent Combat Activity (2020-2025)**
{self._format_section_content(data['recent_activity'])}

**Platform Integration**
{self._format_section_content(data['notable_features'])}

**Export Customers**
{self._format_section_content(data['operators'])}

**Fun Facts**
{self._format_section_content(data['fun_facts'])}"""
        
        return self._add_citations(profile, citations)
    
    def _format_naval_profile(self, threat_name: str, data: Dict[str, str], citations: List[str]) -> str:
        """Format naval threat profile in standardized format."""
        profile = f"""**Threat:** {threat_name}
**Country of Origin:** {data['country_of_origin']}
**Initial Operational Capability:** {data['ioc_date']}
**Primary Role:** {data['primary_role']}

**Class Variants**
{self._format_section_content(data['variants'])}

**Specifications**
{self._format_section_content(data['specifications'])}

**Recent Deployments (2020-2025)**
{self._format_section_content(data['recent_activity'])}

**Notable Capabilities**
{self._format_section_content(data['notable_features'])}

**International Operations**
{self._format_section_content(data['operators'])}

**Fun Facts**
{self._format_section_content(data['fun_facts'])}"""
        
        return self._add_citations(profile, citations)
    
    def _format_ground_system_profile(self, threat_name: str, data: Dict[str, str], citations: List[str]) -> str:
        """Format ground system threat profile in standardized format."""
        profile = f"""**Threat:** {threat_name}
**Country of Origin:** {data['country_of_origin']}
**Initial Operational Capability:** {data['ioc_date']}
**Primary Role:** {data['primary_role']}

**System Variants**
{self._format_section_content(data['variants'])}

**Technical Specifications**
{self._format_section_content(data['specifications'])}

**Recent Deployments (2020-2025)**
{self._format_section_content(data['recent_activity'])}

**Notable Features**
{self._format_section_content(data['notable_features'])}

**Export Customers**
{self._format_section_content(data['operators'])}

**Fun Facts**
{self._format_section_content(data['fun_facts'])}"""
        
        return self._add_citations(profile, citations)
    
    def _format_generic_profile(self, threat_name: str, threat_type: str, data: Dict[str, str], citations: List[str]) -> str:
        """Format generic threat profile for unknown types."""
        profile = f"""**Threat:** {threat_name}
**Type:** {threat_type.replace('_', ' ').title()}
**Country of Origin:** {data['country_of_origin']}
**Initial Operational Capability:** {data['ioc_date']}
**Primary Role:** {data['primary_role']}

**Variants and Configurations**
{self._format_section_content(data['variants'])}

**Technical Specifications**
{self._format_section_content(data['specifications'])}

**Recent Activity (2020-2025)**
{self._format_section_content(data['recent_activity'])}

**Notable Features**
{self._format_section_content(data['notable_features'])}

**International Use**
{self._format_section_content(data['operators'])}

**Fun Facts**
{self._format_section_content(data['fun_facts'])}"""
        
        return self._add_citations(profile, citations)
    
    def _format_section_content(self, content: str) -> str:
        """Format section content with proper bullet points and structure."""
        if content == "Unknown" or not content.strip():
            return "• Information not available"
        
        # If content has multiple lines, format as bullet points
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        if len(lines) > 1:
            return '\n'.join([f"• {line}" for line in lines])
        else:
            return f"• {content.strip()}"
    
    def _add_citations(self, profile: str, citations: List[str]) -> str:
        """Add citations section to the profile."""
        if citations:
            profile += "\n\n**Sources**\n"
            for i, citation in enumerate(citations[:5], 1):  # Limit to 5 citations
                profile += f"{i}. {citation}\n"
        
        return profile
    
    def _format_newsletter_profile(self, threat_name: str, threat_type: str, data: Dict[str, str], citations: List[str]) -> str:
        """Format compact, scannable newsletter format with emoji bullets."""
        # Extract key specs for compact display
        specs = self._extract_key_specs(data['specifications'], threat_type)
        variants = self._extract_key_variants(data['variants'])
        recent_facts = self._extract_recent_facts(data['recent_activity'])
        
        profile = f"**{threat_name}**\n\n"
        
        # Add variants with red triangle emojis
        if variants:
            for variant in variants[:3]:  # Limit to top 3 variants
                profile += f"🔺 {variant}\n"
            profile += "\n"
        
        # Add key specifications in compact format
        if specs:
            profile += f"**Key Specs:** {specs}\n\n"
        
        # Add recent facts with diamond emojis
        if recent_facts:
            for fact in recent_facts[:3]:  # Limit to top 3 facts
                profile += f"🔸 {fact}\n"
        
        return profile
    
    def _format_research_profile(self, threat_name: str, threat_type: str, data: Dict[str, str], citations: List[str]) -> str:
        """Format detailed research format for podcast/transcript use."""
        # Use existing detailed formatting methods
        if threat_type == "aircraft":
            return self._format_aircraft_profile(threat_name, data, citations)
        elif threat_type == "sam_system":
            return self._format_sam_profile(threat_name, data, citations)
        elif threat_type == "munition":
            return self._format_munition_profile(threat_name, data, citations)
        elif threat_type == "naval":
            return self._format_naval_profile(threat_name, data, citations)
        elif threat_type == "ground_system":
            return self._format_ground_system_profile(threat_name, data, citations)
        else:
            return self._format_generic_profile(threat_name, threat_type, data, citations)
    
    def _extract_key_specs(self, specifications: str, threat_type: str) -> str:
        """Extract key specifications for compact display."""
        if specifications == "Unknown" or not specifications.strip():
            return ""
        
        # Look for key metrics based on threat type
        specs = []
        lines = specifications.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Extract speed, range, etc.
            if any(keyword in line.lower() for keyword in ['speed', 'mach', 'km/h', 'mph']):
                specs.append(self._clean_spec_line(line))
            elif any(keyword in line.lower() for keyword in ['range', 'km', 'miles', 'nautical']):
                specs.append(self._clean_spec_line(line))
            elif any(keyword in line.lower() for keyword in ['armament', 'weapon', 'missile']):
                specs.append(self._clean_spec_line(line))
        
        return " | ".join(specs[:3])  # Limit to 3 key specs
    
    def _extract_key_variants(self, variants: str) -> List[str]:
        """Extract key variants for compact display."""
        if variants == "Unknown" or not variants.strip():
            return []
        
        variant_list = []
        lines = variants.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Clean up variant descriptions
            if ':' in line:
                variant_name, description = line.split(':', 1)
                variant_list.append(f"**{variant_name.strip()}:** {description.strip()[:80]}..." if len(description.strip()) > 80 else f"**{variant_name.strip()}:** {description.strip()}")
            else:
                variant_list.append(line[:100] + "..." if len(line) > 100 else line)
        
        return variant_list
    
    def _extract_recent_facts(self, recent_activity: str) -> List[str]:
        """Extract recent facts for compact display."""
        if recent_activity == "Unknown" or not recent_activity.strip():
            return []
        
        facts = []
        lines = recent_activity.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for date patterns and interesting facts
            if any(year in line for year in ['2020', '2021', '2022', '2023', '2024', '2025']):
                # Extract year and key fact
                fact = line[:120] + "..." if len(line) > 120 else line
                facts.append(fact)
        
        return facts
    
    def _clean_spec_line(self, line: str) -> str:
        """Clean up specification lines for compact display."""
        # Remove bullet points and extra formatting
        cleaned = line.replace('•', '').replace('-', '').strip()
        
        # Extract key part if there's a colon
        if ':' in cleaned:
            parts = cleaned.split(':', 1)
            if len(parts) == 2:
                return f"**{parts[0].strip()}:** {parts[1].strip()}"
        
        return cleaned

# Initialize service (will be imported and used with API key)
def create_perplexity_service(api_key: str) -> PerplexityService:
    """Factory function to create PerplexityService with API key."""
    return PerplexityService(api_key)
