def format_hindenburg_time(seconds: float) -> str:
    """
    Converts float seconds to Hindenburg Narrator XML timing format.
    
    Rules:
    - Under 60s: SS.SSS (zero-padded to 2 digits for seconds, e.g., 00.000, 19.480)
    - 60s to 3600s: MM:SS.SSS (zero-padded to 2 digits for minutes and seconds, e.g., 04:24.199)
    - 3600s and above: H:MM:SS.SSS (hours are not padded, e.g., 1:11:02.061)
    
    Args:
        seconds: Time in float seconds.
        
    Returns:
        Hindenburg timing format string.
    """
    if seconds < 0:
        raise ValueError("Time seconds cannot be negative")
        
    # Get milliseconds by rounding the fractional part
    fractional, integral = (seconds - int(seconds)), int(seconds)
    milliseconds = int(round(fractional * 1000))
    
    # Handle rounding carry-over (e.g. 59.9999 -> 60.000)
    if milliseconds >= 1000:
        integral += 1
        milliseconds -= 1000

    if integral < 60:
        return f"{integral:02d}.{milliseconds:03d}"
        
    minutes = (integral // 60) % 60
    secs = integral % 60
    hours = integral // 3600
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}.{milliseconds:03d}"
    else:
        return f"{minutes:02d}:{secs:02d}.{milliseconds:03d}"
