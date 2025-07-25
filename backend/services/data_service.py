import random
import asyncio
from datetime import datetime
from typing import List, Dict, Any
import logging

from schemas.models import EmissionRecord, EnergyRecord
from .external_data_service import ExternalDataService

logger = logging.getLogger(__name__)

class DataService:
    """Service for managing sustainability data"""
    
    def __init__(self):
        self.external_data_service = ExternalDataService()
        self.countries = [
            "United States", "China", "India", "Russia", "Japan", "Germany", 
            "Iran", "South Korea", "Saudi Arabia", "Indonesia", "Canada", 
            "Mexico", "Brazil", "Australia", "United Kingdom", "Italy", 
            "France", "Turkey", "Poland", "Taiwan", "Ukraine", "Thailand",
            "Egypt", "Argentina", "Malaysia", "Netherlands", "Spain", 
            "Pakistan", "Bangladesh", "Vietnam", "Nigeria", "Philippines",
            "South Africa", "Iraq", "Venezuela", "Kazakhstan", "Algeria",
            "Chile", "Morocco", "Peru", "Israel", "Norway", "Finland",
            "Denmark", "Sweden", "Switzerland", "Austria", "Belgium",
            "Portugal", "Czech Republic", "Greece"
        ]
        
        # Base data for more realistic generation
        self.base_emissions = {
            "China": 10065, "United States": 5416, "India": 2654, "Russia": 1711,
            "Japan": 1162, "Germany": 759, "Iran": 720, "South Korea": 616,
            "Saudi Arabia": 517, "Indonesia": 615, "Canada": 572, "Mexico": 475,
            "Brazil": 462, "Australia": 415, "United Kingdom": 351, "Italy": 330,
            "France": 331, "Turkey": 353, "Poland": 340, "Taiwan": 276
        }
        
        self.base_renewable = {
            "Norway": 98.5, "Iceland": 85.0, "Sweden": 74.2, "Finland": 72.9,
            "Denmark": 65.3, "Austria": 62.8, "Switzerland": 62.5, "Canada": 59.3,
            "Brazil": 45.2, "Germany": 41.1, "Spain": 37.5, "United Kingdom": 33.1,
            "Italy": 31.8, "France": 23.4, "Japan": 20.4, "United States": 19.8,
            "China": 28.8, "India": 25.2, "Russia": 19.1, "Australia": 21.2
        }

    async def seed_historical_data(self, db):
        """Seed historical data using real data from external APIs"""
        try:
            emissions_collection = db["emissions"]
            
            # Check if we already have recent real data (not synthetic)
            existing_real_data = await emissions_collection.count_documents({
                "year": {"$gte": 2020},
                "data_source": {"$ne": "synthetic"}
            })
            
            if existing_real_data > 50:  # If we have substantial recent real data
                logger.info("Real historical data already exists, skipping seed")
                return
            
            logger.info("Seeding database with real data from World Bank API...")
            
            # Use external data service to fetch and seed real data
            await self.external_data_service.seed_real_historical_data(db)
            
        except Exception as e:
            logger.error(f"Error seeding historical data: {e}")
            # Fallback to synthetic data if real data fails
            logger.info("Falling back to synthetic data generation...")
            await self._seed_synthetic_data(db)
            raise

    async def _seed_synthetic_data(self, db):
        """Fallback method to seed synthetic data if real data fails"""
        try:
            emissions_collection = db["emissions"]
            energy_collection = db["energy"]
            
            years = range(2010, 2024)  # 2010-2023
            
            # Seed emissions data
            for year in years:
                for country in self.countries:
                    base_emission = self.base_emissions.get(country, random.uniform(50, 1000))
                    
                    # Apply year-over-year growth/decline
                    year_factor = 1 + (year - 2010) * random.uniform(-0.02, 0.03)  # ±2-3% per year
                    co2_emissions = base_emission * year_factor * random.uniform(0.9, 1.1)
                    
                    population = random.randint(1000000, 1400000000)
                    gdp = random.uniform(100, 25000)
                    co2_per_capita = (co2_emissions * 1000000) / population
                    
                    record = {
                        "country": country,
                        "year": year,
                        "co2_emissions": round(co2_emissions, 2),
                        "population": population,
                        "gdp": round(gdp, 2),
                        "co2_per_capita": round(co2_per_capita, 2),
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                        "data_source": "synthetic"
                    }
                    
                    await emissions_collection.insert_one(record)
            
            # Seed energy data
            for year in years:
                for country in self.countries:
                    base_renewable = self.base_renewable.get(country, random.uniform(5, 40))
                    
                    # Apply year-over-year growth for renewables
                    year_factor = 1 + (year - 2010) * random.uniform(0.02, 0.08)  # 2-8% growth per year
                    renewable_percentage = min(100, base_renewable * year_factor * random.uniform(0.9, 1.1))
                    
                    total_energy = random.uniform(50, 4000)
                    renewable_energy = total_energy * (renewable_percentage / 100)
                    fossil_fuel_energy = total_energy - renewable_energy
                    
                    record = {
                        "country": country,
                        "year": year,
                        "renewable_percentage": round(renewable_percentage, 2),
                        "total_energy_consumption": round(total_energy, 2),
                        "renewable_energy": round(renewable_energy, 2),
                        "fossil_fuel_energy": round(fossil_fuel_energy, 2),
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                        "data_source": "synthetic"
                    }
                    
                    await energy_collection.insert_one(record)
            
            logger.info(f"Seeded synthetic data for {len(years)} years and {len(self.countries)} countries")
            
        except Exception as e:
            logger.error(f"Error seeding synthetic data: {e}")
            raise