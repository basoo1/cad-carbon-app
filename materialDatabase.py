"""
Module: materialDatabase.py
Purpose:
    Maintains the centralized material property matrix for mechanical,
    thermal, economic, and ecological analysis.
    
    All numerical units are strictly standardized:
    - Density: g/cm^3
    - Strength and Elastic Modulus: MPa and GPa
    - Coefficient of Thermal Expansion (CTE): ppm/K (1e-6 / K)
    - Specific Heat / Thermal Conductivity: W/(m*K)
    - Embodied Carbon: kg CO2e / kg (ICE Database / NIST baselines)
    - Cost: USD / kg
"""

materialDatabase = {
    "virginAluminum6061T6": {
        "displayName": "Virgin Aluminum 6061-T6",
        "category": "metal",
        "densityGcm3": 2.70,
        "yieldStrengthMpa": 276.0,
        "ultimateStrengthMpa": 310.0,
        "elasticModulusGpa": 68.9,
        "poissonRatio": 0.33,
        "thermalExpansionPpmK": 23.4,
        "thermalConductivityWmK": 167.0,
        "maxServiceTempC": 150.0,
        "corrosionResistance": "good",
        "uvResistance": "excellent",
        "costPerKgUsd": 3.80,
        "carbonFactorKgCo2ePerKg": 11.50
    },
    "recycledAluminum6061": {
        "displayName": "Recycled Aluminum 6061",
        "category": "metal",
        "densityGcm3": 2.70,
        "yieldStrengthMpa": 260.0,
        "ultimateStrengthMpa": 295.0,
        "elasticModulusGpa": 68.0,
        "poissonRatio": 0.33,
        "thermalExpansionPpmK": 23.4,
        "thermalConductivityWmK": 160.0,
        "maxServiceTempC": 150.0,
        "corrosionResistance": "good",
        "uvResistance": "excellent",
        "costPerKgUsd": 3.40,
        "carbonFactorKgCo2ePerKg": 1.70
    },
    "structuralSteelA36": {
        "displayName": "Structural Steel (A36)",
        "category": "metal",
        "densityGcm3": 7.85,
        "yieldStrengthMpa": 250.0,
        "ultimateStrengthMpa": 400.0,
        "elasticModulusGpa": 200.0,
        "poissonRatio": 0.26,
        "thermalExpansionPpmK": 12.0,
        "thermalConductivityWmK": 51.9,
        "maxServiceTempC": 380.0,
        "corrosionResistance": "poor",
        "uvResistance": "excellent",
        "costPerKgUsd": 1.10,
        "carbonFactorKgCo2ePerKg": 1.80
    },
    "stainlessSteel304": {
        "displayName": "Stainless Steel 304",
        "category": "metal",
        "densityGcm3": 8.00,
        "yieldStrengthMpa": 215.0,
        "ultimateStrengthMpa": 505.0,
        "elasticModulusGpa": 193.0,
        "poissonRatio": 0.29,
        "thermalExpansionPpmK": 17.3,
        "thermalConductivityWmK": 16.2,
        "maxServiceTempC": 800.0,
        "corrosionResistance": "excellent",
        "uvResistance": "excellent",
        "costPerKgUsd": 4.50,
        "carbonFactorKgCo2ePerKg": 4.50
    },
    "titaniumGrade5": {
        "displayName": "Titanium (Ti-6Al-4V Grade 5)",
        "category": "metal",
        "densityGcm3": 4.43,
        "yieldStrengthMpa": 880.0,
        "ultimateStrengthMpa": 950.0,
        "elasticModulusGpa": 113.8,
        "poissonRatio": 0.34,
        "thermalExpansionPpmK": 8.6,
        "thermalConductivityWmK": 6.7,
        "maxServiceTempC": 400.0,
        "corrosionResistance": "excellent",
        "uvResistance": "excellent",
        "costPerKgUsd": 32.00,
        "carbonFactorKgCo2ePerKg": 35.00
    },
    "absGeneric": {
        "displayName": "ABS Plastic (Injection Grade)",
        "category": "polymer",
        "densityGcm3": 1.05,
        "yieldStrengthMpa": 40.0,
        "ultimateStrengthMpa": 45.0,
        "elasticModulusGpa": 2.3,
        "poissonRatio": 0.35,
        "thermalExpansionPpmK": 73.8,
        "thermalConductivityWmK": 0.18,
        "maxServiceTempC": 80.0,
        "corrosionResistance": "good",
        "uvResistance": "poor",
        "costPerKgUsd": 2.20,
        "carbonFactorKgCo2ePerKg": 3.10
    },
    "recycledPetg": {
        "displayName": "Recycled PETG (rPETG)",
        "category": "polymer",
        "densityGcm3": 1.27,
        "yieldStrengthMpa": 50.0,
        "ultimateStrengthMpa": 55.0,
        "elasticModulusGpa": 2.1,
        "poissonRatio": 0.38,
        "thermalExpansionPpmK": 60.0,
        "thermalConductivityWmK": 0.19,
        "maxServiceTempC": 70.0,
        "corrosionResistance": "good",
        "uvResistance": "good",
        "costPerKgUsd": 1.90,
        "carbonFactorKgCo2ePerKg": 1.45
    },
    "pa6Gf30": {
        "displayName": "PA6-GF30 (30% Glass-Filled Nylon)",
        "category": "composite",
        "densityGcm3": 1.35,
        "yieldStrengthMpa": 175.0,
        "ultimateStrengthMpa": 185.0,
        "elasticModulusGpa": 8.5,
        "poissonRatio": 0.35,
        "thermalExpansionPpmK": 30.0,
        "thermalConductivityWmK": 0.28,
        "maxServiceTempC": 140.0,
        "corrosionResistance": "good",
        "uvResistance": "good",
        "costPerKgUsd": 4.20,
        "carbonFactorKgCo2ePerKg": 5.20
    },
    "polycarbonate": {
        "displayName": "Polycarbonate (PC)",
        "category": "polymer",
        "densityGcm3": 1.20,
        "yieldStrengthMpa": 65.0,
        "ultimateStrengthMpa": 72.0,
        "elasticModulusGpa": 2.4,
        "poissonRatio": 0.37,
        "thermalExpansionPpmK": 65.0,
        "thermalConductivityWmK": 0.20,
        "maxServiceTempC": 120.0,
        "corrosionResistance": "good",
        "uvResistance": "good",
        "costPerKgUsd": 3.60,
        "carbonFactorKgCo2ePerKg": 6.00
    }
}


def getMaterialData(materialKey):
    """
    Retrieves the complete property map for a specific material key.
    Returns None if the key is not defined.
    """
    return materialDatabase.get(materialKey, None)


def listAllMaterialKeys():
    """
    Returns an array containing all material keys available in the database.
    """
    return list(materialDatabase.keys())


def getAllMaterialsSummary():
    """
    Flattens the material database into an array of dictionaries.
    This serialized structure is passed directly to the Gemini LLM reasoning context
    and Plotly Ashby scatter visualizer.
    """
    summaryList = []
    for materialKey, materialData in materialDatabase.items():
        summaryList.append({
            "key": materialKey,
            "name": materialData["displayName"],
            "category": materialData["category"],
            "yieldMpa": materialData["yieldStrengthMpa"],
            "modulusGpa": materialData["elasticModulusGpa"],
            "ctePpmK": materialData["thermalExpansionPpmK"],
            "maxTempC": materialData["maxServiceTempC"],
            "corrosion": materialData["corrosionResistance"],
            "uv": materialData["uvResistance"],
            "costUsdKg": materialData["costPerKgUsd"],
            "carbonCo2eKg": materialData["carbonFactorKgCo2ePerKg"]
        })
    return summaryList