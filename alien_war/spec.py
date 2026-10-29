"""Timing, captions and HUD stats for "What if aliens declared war on Earth?" (fictional)."""
import math
DUR = 62.0
FPS = 30
CHANNEL = "@YourChannel"
TAG = "Fictional scenario. Not a prediction."

TITLE = [(0.3, 6.6, "What if aliens declared war on Earth?"),
         (58.4, 62.0, "Would you have fought, or run?")]

# (t_in, t_out, text) - every line is timed to the event it describes
CAPS = [
    (2.4, 4.6, "7:42 PM. A normal evening in the city."),
    (4.8, 7.0, "Until every sky on Earth goes dark."),
    (7.4, 10.4, "Seventeen ships. One above every capital."),
    (10.6, 14.9, "No demands. No messages. Just a countdown."),
    (15.2, 18.0, "Their first strike wasn't a bomb."),
    (18.3, 21.2, "It was the power grid. Every plant on Earth, gone in 11 seconds."),
    (21.5, 24.0, "No lights. No phones. No internet."),
    (24.3, 28.0, "Day 2. Every army launches everything it has."),
    (28.3, 32.9, "4,200 missiles. Zero damage. Their shield held."),
    (33.3, 36.6, "Day 9. A lab in Geneva notices something."),
    (36.8, 39.6, "Their shield drops for 0.4 seconds every time they fire."),
    (39.8, 41.9, "That's the window. We only get one shot."),
    (42.3, 45.4, "Day 10. 40,000 aircraft. One coordinated strike."),
    (45.6, 48.6, "Half of them never come back."),
    (48.8, 51.9, "But when the shield blinks, six missiles slip through."),
    (52.4, 55.4, "The fleet fell in three minutes."),
    (55.6, 58.3, "Humanity lost two billion people."),
]
END = (59.4, CHANNEL, "Follow for more what-ifs")


def mmss(x):
    x = max(0.0, x)
    return f"{int(x // 60)}:{int(x % 60):02d}.{int((x % 1) * 100):02d}"


def stat(t):
    if 0.5 <= t < 7.0:
        return ("ALIEN FLEET ARRIVES IN", mmss(7.0 - t), "SIGNAL SOURCE: UNKNOWN")
    if 7.2 <= t < 11.0:
        n = 1 + int(16 * min(1, (t - 7.4) / 3.2))
        return ("ALIEN SHIPS IN ORBIT", str(max(1, n)), "ONE ABOVE EVERY CAPITAL")
    if 11.0 <= t < 15.0:
        return ("FIRST STRIKE IN", mmss(15.0 - t), "NO WARNING GIVEN")
    if 15.3 <= t < 24.0:
        p = max(0.0, 1 - (t - 15.6) / 7.2)
        return ("GLOBAL POWER GRID", f"{int(round(p * 100))}%", "EVERY PLANT ON EARTH")
    if 24.3 <= t < 33.0:
        f = max(0.0, min(1.0, (t - 24.4) / 7.6)) ** 1.4
        return ("MISSILES FIRED", f"{int(4200 * f):,}", "SUCCESSFUL HITS: 0")
    if 33.3 <= t < 42.0:
        v = 0.4 * min(1.0, max(0.0, (t - 36.6) / 2.0))
        return ("SHIELD DOWN TIME", f"{v:.1f} s", "EVERY TIME THEY FIRE")
    if 42.2 <= t < 52.0:
        f = max(0.0, min(1.0, (t - 42.4) / 6.0))
        ships = 17 if t > 51.0 else 0
        return ("AIRCRAFT LOST", f"{int(19800 * f):,}", f"ALIEN SHIPS DOWN: {ships}")
    if 52.3 <= t < 58.3:
        f = max(0.0, min(1.0, (t - 52.5) / 4.5))
        return ("HUMANS REMAINING", f"{8.1 - 2.0 * f:.1f} billion", "STARTED AT 8.1 BILLION")
    return None
