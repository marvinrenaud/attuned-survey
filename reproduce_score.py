from backend.src.scoring.power import calculate_power_dynamic

def test_scores():
    # Scenario: User answers 6 (Agree) to all power questions
    answers = {
        'A13': 6, # Top
        'A15': 6, # Top
        'A14': 6, # Bottom
        'A16': 6  # Bottom
    }
    
    result = calculate_power_dynamic(answers)
    print(f"Inputs: {answers}")
    print(f"Result: {result}")

if __name__ == "__main__":
    test_scores()
