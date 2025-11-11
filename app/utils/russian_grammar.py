"""Russian grammar utilities for proper number declension."""


def format_years_russian(years: float) -> str:
    """
    Format years with correct Russian declension.
    
    Russian declension rules:
    - 1, 21, 31, ... → год (year)
    - 2, 3, 4, 22, 23, 24, ... → года (years, genitive singular)
    - 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 25, 26, ... → лет (years, genitive plural)
    
    Args:
        years: Number of years (float)
        
    Returns:
        Formatted string with correct declension
    """
    # Convert to integer for declension rules
    years_int = int(years)
    
    # Get last digit and last two digits for declension rules
    last_digit = years_int % 10
    last_two_digits = years_int % 100
    
    # Special cases: 11-14 always use "лет"
    if 11 <= last_two_digits <= 14:
        return f"{years_int} лет"
    
    # Cases based on last digit
    if last_digit == 1:
        return f"{years_int} год"
    elif last_digit in [2, 3, 4]:
        return f"{years_int} года"
    else:  # 0, 5, 6, 7, 8, 9
        return f"{years_int} лет"


def format_years_english(years: float) -> str:
    """
    Format years in English.
    
    Args:
        years: Number of years (float)
        
    Returns:
        Formatted string
    """
    years_int = int(years)
    if years_int == 1:
        return "1 year"
    else:
        return f"{years_int} years"

