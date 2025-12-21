from backend.src.scoring.arousal import calculate_arousal_propensity

def test_arousal():
    # Scenario: User answers 6 (Agree) to all arousal questions (A1-A12)
    answers = {f'A{i}': 6 for i in range(1, 13)}
    
    result = calculate_arousal_propensity(answers)
    print(f"Inputs: All 6s")
    print(f"Result: {result}")

if __name__ == "__main__":
    test_arousal()
