
from dataclasses import dataclass, field
from typing import List

@dataclass
class PlayEvent:
    event_type: str          # "single", "double", "out", etc.
    inning: int
    top_or_bottom: str
    player_name: str = ""    # empty for now, ready for later
    notes: str = ""          # anything extra you want to log

@dataclass
class GameState:
    inning: int = 1
    top_or_bottom: str = "top"
    outs: int = 0
    bases: List[bool] = field(default_factory=lambda: [False, False, False])
    home_score: int = 0
    away_score: int = 0
    
    play_log: List[PlayEvent] = field(default_factory=list)
    
    def add_out(self):
        self.outs += 1
        if self.outs >= 3:
            self._end_half_inning()

    def _end_half_inning(self):
        self.outs = 0
        self.bases = [False, False, False]
        if self.top_or_bottom == "top":
            self.top_or_bottom = "bottom"
        else:
            self.top_or_bottom = "top"
            self.inning += 1
            
    def record_play(self, batter: str, runners: dict, event_type: str):
        """
        batter:     "out" | "1b" | "2b" | "3b" | "hr" | "walk"
        runners:    { from_base(int): to_base(int|"score"|"out") }
                    e.g. {0: 1, 2: "score"}
        event_type: human label for the log e.g. "single", "sac_bunt"
        """
        runs_scored = 0
        new_bases = [False, False, False]
    
        # resolve all baserunners first
        for from_base, to_base in runners.items():
            from_base = int(from_base)
            if not self.bases[from_base]:
                raise ValueError(f"No runner on base {from_base}")
            if to_base == "score":
                runs_scored += 1
            elif to_base == "out":
                self.add_out()
            else:
                new_bases[int(to_base)] = True
    
        # place batter
        batter_base = {"1b": 0, "2b": 1, "3b": 2}
        if batter == "hr":
            runs_scored += 1
        elif batter == "out":
            self.add_out()
        elif batter in batter_base:
            new_bases[batter_base[batter]] = True
        # walk: batter goes to 1st, but only if not forced by runners dict already
        elif batter == "walk":
            if not new_bases[0]:
                new_bases[0] = True
    
        self.bases = new_bases
    
        # update score
        if self.top_or_bottom == "top":
            self.away_score += runs_scored
        else:
            self.home_score += runs_scored
    
        # log it
        self.play_log.append(PlayEvent(
            event_type=event_type,
            inning=self.inning,
            top_or_bottom=self.top_or_bottom
        ))
    
def assert_equal(label, actual, expected):
    status = "PASS" if actual == expected else "FAIL"
    print(f"[{status}] {label}")
    if actual != expected:
        print(f"       expected: {expected}")
        print(f"       got:      {actual}")

if __name__ == "__main__":

    # --- Test 1: clean single, no runners ---
    g = GameState()
    g.record_play("1b", {}, "single")
    assert_equal("single, no runners → batter on 1st", g.bases, [True, False, False])
    assert_equal("single, no runners → no score", g.away_score, 0)

    # --- Test 2: single, runner on 2nd scores ---
    g = GameState()
    g.bases = [False, True, False]
    g.record_play("1b", {1: "score"}, "single")
    assert_equal("single, runner on 2nd scores → 1pt", g.away_score, 1)
    assert_equal("single, runner on 2nd scores → batter on 1st", g.bases, [True, False, False])

    # --- Test 3: home run, bases loaded ---
    g = GameState()
    g.bases = [True, True, True]
    g.record_play("hr", {0: "score", 1: "score", 2: "score"}, "home_run")
    assert_equal("grand slam → 4 runs", g.away_score, 4)
    assert_equal("grand slam → bases empty", g.bases, [False, False, False])

    # --- Test 4: sac bunt, runners on 1st and 2nd ---
    g = GameState()
    g.bases = [True, True, False]
    g.record_play("out", {0: 1, 1: 2}, "sac_bunt")
    assert_equal("sac bunt → 1 out", g.outs, 1)
    assert_equal("sac bunt → runners advanced", g.bases, [False, True, True])

    # --- Test 5: fielder's choice, runner on 1st thrown out ---
    g = GameState()
    g.bases = [True, False, False]
    g.record_play("1b", {0: "out"}, "fielders_choice")
    assert_equal("FC → runner out", g.outs, 1)
    assert_equal("FC → batter safe at 1st", g.bases, [True, False, False])

    # --- Test 6: 3 outs flips the inning ---
    g = GameState()
    g.record_play("out", {}, "groundout")
    g.record_play("out", {}, "groundout")
    g.record_play("out", {}, "groundout")
    assert_equal("3 outs → outs reset", g.outs, 0)
    assert_equal("3 outs → flips to bottom", g.top_or_bottom, "bottom")
    assert_equal("3 outs → still inning 1", g.inning, 1)

    # --- Test 7: end of bottom flips to next inning ---
    g = GameState()
    g.top_or_bottom = "bottom"
    g.record_play("out", {}, "groundout")
    g.record_play("out", {}, "groundout")
    g.record_play("out", {}, "groundout")
    assert_equal("bottom 3 outs → inning 2", g.inning, 2)
    assert_equal("bottom 3 outs → back to top", g.top_or_bottom, "top")

    # --- Test 8: play log records correctly ---
    g = GameState()
    g.record_play("1b", {}, "single")
    g.record_play("hr", {0: "score"}, "home_run")
    assert_equal("play log has 2 entries", len(g.play_log), 2)
    assert_equal("play log entry 2 is home_run", g.play_log[1].event_type, "home_run")

    print("\nDone.")
