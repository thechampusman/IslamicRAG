import math
from datetime import datetime, date, timedelta
import pytz

# Minimal prayer time calculations for sunset and isha using solar geometry.
# Method: MWL style twilight angle for Isha = 17 degrees below horizon.

def _deg2rad(d: float) -> float:
    return d * math.pi / 180.0

def _rad2deg(r: float) -> float:
    return r * 180.0 / math.pi

def _julian_day(d: date) -> float:
    y = d.year
    m = d.month
    dd = d.day
    if m <= 2:
        y -= 1
        m += 12
    A = math.floor(y / 100)
    B = 2 - A + math.floor(A / 4)
    jd = math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1)) + dd + B - 1524.5
    return jd

def _sun_position(jd: float):
    D = jd - 2451545.0
    g = _deg2rad((357.529 + 0.98560028 * D) % 360)  # mean anomaly
    q = (280.459 + 0.98564736 * D) % 360            # mean longitude
    L = _deg2rad((q + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g)) % 360)  # ecliptic longitude
    e = _deg2rad(23.439 - 0.00000036 * D)           # obliquity
    RA = math.atan2(math.cos(e) * math.sin(L), math.cos(L))
    RA_deg = (_rad2deg(RA)) % 360
    dec = math.asin(math.sin(e) * math.sin(L))
    # Equation of time (in minutes)
    q_rad = _deg2rad(q)
    EoT = 4 * _rad2deg(q_rad - RA)
    return dec, EoT  # declination (rad), equation of time (minutes)

def _solar_noon(longitude: float, tz_offset_min: float, jd: float) -> float:
    dec, eot = _sun_position(jd)
    # solar noon in minutes from midnight local time
    noon = 720 - 4 * longitude + tz_offset_min - eot
    return noon

def _hour_angle(lat_rad: float, dec: float, solar_altitude_deg: float) -> float:
    # altitude negative for sun below horizon (e.g., -0.833 for sunset, -17 for isha)
    alt = _deg2rad(solar_altitude_deg)
    cosH = (math.sin(alt) - math.sin(lat_rad) * math.sin(dec)) / (math.cos(lat_rad) * math.cos(dec))
    # Guard numeric domain
    if cosH <= -1:
        H = math.pi  # 180°
    elif cosH >= 1:
        H = 0.0
    else:
        H = math.acos(cosH)
    return H

def compute_sunset_and_isha(lat: float, lon: float, d: date, tz_name: str = "Asia/Kolkata", isha_angle: float = 17.0):
    tz = pytz.timezone(tz_name)
    # get local date start to determine tz offset for that date
    local_dt = tz.localize(datetime(d.year, d.month, d.day, 12, 0, 0))
    tz_offset_min = local_dt.utcoffset().total_seconds() / 60.0

    jd = _julian_day(d)
    dec, eot = _sun_position(jd)

    lat_rad = _deg2rad(lat)
    # Solar noon (minutes from midnight)
    noon_min = _solar_noon(lon, tz_offset_min, jd)

    # Sunset altitude uses -0.833 degrees (standard refraction/solar radius)
    H_sunset = _hour_angle(lat_rad, dec, -0.833)
    sunset_min = noon_min + _rad2deg(H_sunset) * 4  # 1 degree = 4 minutes

    # Isha angle below horizon
    H_isha = _hour_angle(lat_rad, dec, -abs(isha_angle))
    isha_min = noon_min + _rad2deg(H_isha) * 4

    # Convert to localized datetime
    base_day = tz.localize(datetime(d.year, d.month, d.day))
    sunset_dt = base_day + timedelta(minutes=sunset_min)
    isha_dt = base_day + timedelta(minutes=isha_min)
    return sunset_dt, isha_dt


def compute_prayer_times(
    lat: float,
    lon: float,
    d: date,
    tz_name: str = "Asia/Kolkata",
    method: str = "MWL",
    asr: str = "standard",
):
    """
    Compute a simple daily timetable (approximate) using solar angles.
    - Fajr angle: 18° (MWL), 15° (ISNA), 18.5° (Egypt), 18.5/90 (Umm al-Qura special), etc.
    - Isha angle: 17° (MWL), 15° (ISNA), 17.5° (Egypt), 90-min after Maghrib (Umm al-Qura typical outside Ramadan).
    - Dhuhr: solar noon + ~1 min offset
    - Asr: shadow factor 1 (standard/Shafi'i) or 2 (Hanafi)
    - Maghrib: sunset at altitude -0.833°
    Note: This is a simplified approximation for local, educational purposes.
    """

    method = (method or "MWL").upper()
    asr = (asr or "standard").lower()

    # Angle presets and labels
    fajr_angle = 18.0
    isha_angle = 17.0
    isha_fixed_after_maghrib_min = None
    method_labels = {
        "MWL": "Muslim World League",
        "ISNA": "Islamic Society of North America",
        "EGYPT": "Egyptian General Authority of Survey",
        "UMM_AL_QURA": "Umm al-Qura University, Makkah",
        "KARACHI": "University of Islamic Sciences, Karachi",
    }
    if method == "ISNA":
        fajr_angle = 15.0
        isha_angle = 15.0
    elif method in ("EGYPT", "EGYPTIAN"):
        fajr_angle = 19.5
        isha_angle = 17.5
        method = "EGYPT"
    elif method in ("UMM_AL_QURA", "UMM AL QURA", "UMMALQURA"):
        fajr_angle = 18.5
        isha_fixed_after_maghrib_min = 90
        method = "UMM_AL_QURA"
    elif method in ("KARACHI", "UNIVERSITY_OF_ISLAMIC_SCIENCES", "UISK"):
        fajr_angle = 18.0
        isha_angle = 18.0
        method = "KARACHI"

    tz = pytz.timezone(tz_name)
    local_dt = tz.localize(datetime(d.year, d.month, d.day, 12, 0, 0))
    tz_offset = local_dt.utcoffset()
    tz_offset_min = tz_offset.total_seconds() / 60.0 if tz_offset else 0

    jd = _julian_day(d)
    dec, eot = _sun_position(jd)
    lat_rad = _deg2rad(lat)

    # Solar noon in minutes from midnight
    noon_min = _solar_noon(lon, tz_offset_min, jd)

    # Helper to convert altitude angle to time offset from noon
    def minutes_from_noon_for_alt(alt_deg: float) -> float:
        H = _hour_angle(lat_rad, dec, alt_deg)
        return _rad2deg(H) * 4

    # Sunrise / Sunset
    sun_alt = -0.833
    sunrise_min = noon_min - minutes_from_noon_for_alt(sun_alt)
    sunset_min = noon_min + minutes_from_noon_for_alt(sun_alt)

    # Fajr: Sun at -fajr_angle
    fajr_min = noon_min - minutes_from_noon_for_alt(-abs(fajr_angle))

    # Dhuhr: solar noon (+ small offset)
    dhuhr_min = noon_min + 1

    # Asr: shadow factor 1 for standard, 2 for Hanafi
    # Formula: altitude where shadow length equals factor (1 or 2)
    # tan(alt) = 1 / (factor + tan(|lat - dec|)) approximate via standard method
    # Use classical formula: H = arccos((sin(arctan(1/f + tan(|lat - dec|))) - sin(phi) sin(dec)) / (cos(phi) cos(dec)))
    factor = 1 if asr in ("standard", "shafii", "shafii") else 2
    # Compute angle for asr
    # Altitude for asr when the shadow ratio = factor:
    # alt_asr = arctan(1/(factor + tan(|phi - dec|)))
    alt_asr = math.atan(1.0 / (factor + abs(math.tan(lat_rad - dec))))
    alt_asr_deg = _rad2deg(alt_asr)
    asr_min = noon_min + minutes_from_noon_for_alt(alt_asr_deg)

    # Maghrib: sunset
    maghrib_min = sunset_min

    # Isha: angle-based or fixed offset (for Umm al-Qura)
    if isha_fixed_after_maghrib_min is not None:
        isha_min = maghrib_min + isha_fixed_after_maghrib_min
    else:
        isha_min = noon_min + minutes_from_noon_for_alt(-abs(isha_angle))

    # Build localized datetimes
    base_day = tz.localize(datetime(d.year, d.month, d.day))
    def to_dt(mins: float) -> datetime:
        return base_day + timedelta(minutes=mins)

    times = {
        "Fajr": to_dt(fajr_min),
        "Sunrise": to_dt(sunrise_min),
        "Dhuhr": to_dt(dhuhr_min),
        "Asr": to_dt(asr_min),
        "Maghrib": to_dt(maghrib_min),
        "Isha": to_dt(isha_min),
        "metadata": {
            "method": method,
            "method_label": method_labels.get(method, method),
            "asr": asr,
            "tz": tz_name,
            "offset_min": int(tz_offset_min),
            "fajr_angle": fajr_angle,
            "isha_angle": isha_angle,
        }
    }
    return times
