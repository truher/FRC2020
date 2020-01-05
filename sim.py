#!/usr/bin/env python

from random import randint
import copy
import math

MATCH_SEC = 120

class Agent:
    def __init__(self, role, route, rng, target, zone):
        self.role = role # [shooter, rebounder, guard, defender]
        self.route = route # [trench, outside]
        self.rng = rng # [short, medium, long]
        self.target = target # [low, high, inner]
        self.zone = zone # [target, center, supply]
    def __str__(self):
        return (f"role: {self.rolestr()}"
                f", route: {self.routestr()}"
                f", range: {self.rangestr()}"
                f", target: {self.targetstr()}"
                f", zone: {self.zonestr()}")
    def rolestr(self):
        if self.role == 1: return "shooter"
        if self.role == 2: return "rebounder"
        if self.role == 3: return "guard"
        if self.role == 4: return "defender"
    def routestr(self):
        if self.route == 1: return "trench"
        if self.route == 2: return "outside"
    def rangestr(self):
        if self.rng == 1: return "short"
        if self.rng == 2: return "medium"
        if self.rng == 3: return "long"
    def targetstr(self):
        if self.target == 1: return "low"
        if self.target == 2: return "high"
        if self.target == 3: return "inner"
    def zonestr(self):
        if self.zone == 1: return "target"
        if self.zone == 2: return "center"
        if self.zone == 3: return "supply"


def randAgent():
    return Agent(randint(1,4), randint(1,2), randint(1,3), randint(1,3), randint(1,3))

def isTargetDefender(opp):
    return opp.role == 4 and opp.zone == 1

def isCenterDefender(opp):
    return opp.role == 4 and opp.zone == 2

def isSupplyDefender(opp):
    return opp.role == 4 and opp.zone == 3

# speed is time to get across the field
def cycleTime(shooter, opp1, opp2, opp3, defense_effectiveness, speed):
    if shooter.role != 1 and shooter.role != 2:
        return 0
    defense = 1.0 # default = no defense
    uncontested_cycle_time = 0
    LOAD = 5 
    SHOOT = 5 
    if shooter.rng == 1: # short
        uncontested_cycle_time = LOAD + speed + SHOOT + speed
        if shooter.route == 1: # inside
            if (isSupplyDefender(opp1) or isSupplyDefender(opp2) or isSupplyDefender(opp3)
                or isTargetDefender(opp1) or isTargetDefender(opp2) or isTargetDefender(opp3)):
                defense = defense_effectiveness # inside is slowed at the ends
        elif shooter.route == 2:
            if (isSupplyDefender(opp1) or isSupplyDefender(opp2) or isSupplyDefender(opp3)
                or isCenterDefender(opp1) or isCenterDefender(opp2) or isCenterDefender(opp3)
                or isTargetDefender(opp1) or isTargetDefender(opp2) or isTargetDefender(opp3)):
                defense = defense_effectiveness # outside is slowed everywhere
    elif shooter.rng == 2: # med
        uncontested_cycle_time = LOAD + 0.75 * speed + SHOOT + 0.75 * speed
        if shooter.route == 1: # inside
            if (isSupplyDefender(opp1) or isSupplyDefender(opp2) or isSupplyDefender(opp3)):
                defense = defense_effectiveness # inside is slowed at the ends
        elif shooter.route == 2:
            if (isSupplyDefender(opp1) or isSupplyDefender(opp2) or isSupplyDefender(opp3)
                or isCenterDefender(opp1) or isCenterDefender(opp2) or isCenterDefender(opp3)):
                defense = defense_effectiveness # outside is slowed everywhere
    elif shooter.rng == 3: # long
        uncontested_cycle_time = LOAD + 0.25 * speed + SHOOT + 0.25 * speed
        if (isSupplyDefender(opp1) or isSupplyDefender(opp2) or isSupplyDefender(opp3)):
            defense = defense_effectiveness # inside is slowed at the ends
    return uncontested_cycle_time * defense

def percentage(shooter, opp1, opp2, opp3, defense_effectiveness, accuracy):
    if shooter.role != 1 and shooter.role != 2:
        return 0
    defense = 1.0 # default = no defense
    uncontested_pct = 0.0
    if shooter.rng == 1: # short
        if isTargetDefender(opp1) or isTargetDefender(opp2) or isTargetDefender(opp3):
            defense = defense_effectiveness # contested shots are lower percentage
        if shooter.target == 1: # low
            uncontested_pct = 1.0
        elif shooter.target == 2: # high
            uncontested_pct = accuracy
        elif shooter.target == 3: # inner
            uncontested_pct = 0.0 # can't reach inner from short
    elif shooter.rng == 2: # med
        if isCenterDefender(opp1) or isCenterDefender(opp2) or isCenterDefender(opp3):
            if shooter.route == 1:
                defense = 1.0 # trench shots cannot be contested
            elif shooter.route == 2:
                defense = defense_effectiveness # outside shots can be contested
        if shooter.target == 1: # low
            uncontested_pct = accuracy
        elif shooter.target == 2: 
            uncontested_pct = accuracy # high is the same as low from medium range
        elif shooter.target == 3: # inner
            if shooter.route == 1:
                uncontested_pct = 0.0 # trench shots cannot reach inner
            elif shooter.route == 2:
                uncontested_pct = accuracy ** 2
    elif shooter.rng == 3: # long
        if isSupplyDefender(opp1) or isSupplyDefender(opp2) or isSupplyDefender(opp3):
            defense = defense_effectiveness # contested shots are lower percentage
        if shooter.target == 1: # low
            uncontested_pct = 0.0 # long low shots are impossible
        elif shooter.target == 2: # high
            uncontested_pct = accuracy ** 3 # long high shots are pretty hard
        elif shooter.target == 3: # inner
            uncontested_pct = 0.0 # long inner shots are impossible
    return uncontested_pct / defense

def shots(shooter, opp1, opp2, opp3, defense_effectiveness, speed):
    if shooter.role != 1 and shooter.role != 2:
        return 0
    cyc = cycleTime(shooter, opp1, opp2, opp3, defense_effectiveness, speed)
    if cyc == 0:
        return 0
    return 5 * MATCH_SEC // cyc # assume infinite supply

def looseBalls(shooter, opp1, opp2, opp3, defense_effectiveness, accuracy, speed):
    return (shots(shooter, opp1, opp2, opp3, defense_effectiveness, speed)
            * (1 - percentage(shooter, opp1, opp2, opp3, defense_effectiveness, accuracy)))

def isPasser(shooter): # special case, long low = passing to rebounder
    return shooter.role == 1 and shooter.rng == 3 and shooter.target == 1

def rebounds(same1, opp1, opp2, opp3, defense_effectiveness, accuracy, speed): # ignores second rebounds
    if same1.role != 1:
        return 0,0
    balls = looseBalls(same1, opp1, opp2, opp3, defense_effectiveness, accuracy, speed)
    fetch_time_sec = (2 if isPasser(same1) else 4) # TODO: sensitivity?
    shot_time_sec = 1 # TODO: is this right?
    cycle_time = fetch_time_sec + shot_time_sec
    balls_shot = min(balls, MATCH_SEC/cycle_time)
    return balls_shot, cycle_time

def totalRebounds(balls_shot1, cycle_time1, balls_shot2, cycle_time2):
    remaining_time = MATCH_SEC - balls_shot1 * cycle_time1
    if cycle_time2 == 0:
        return balls_shot1
    remaining_balls = min(balls_shot2, remaining_time // cycle_time2)
    return balls_shot1 + remaining_balls

def ballScore(shooter, scored_balls):
    if shooter.target == 1:
        return scored_balls
    elif shooter.target == 2:
        return scored_balls * 2
    elif shooter.target == 3:
        return scored_balls * 3

def scoreImpl(me, same1, same2, opp1, opp2, opp3, defense_effectiveness, accuracy, speed, debug=False):
    if me.role == 1:  # shooter
        shot_cnt = shots(me, opp1, opp2, opp3, defense_effectiveness, speed)
        pct = percentage(me, opp1, opp2, opp3, defense_effectiveness, accuracy)
        scored_balls = math.floor(shot_cnt * pct)
        misses = shot_cnt - scored_balls
        if debug: print(f"shooter [{me}] shots {shot_cnt} pct {pct} scores {scored_balls} misses {misses}")
        return ballScore(me, scored_balls)
    elif me.role == 2: # rebounder
        score = 0
        if same1.role == 1 and same2.role == 1: # two shooters
            balls_shot1, cycle_time1 = rebounds(same1, opp1, opp2, opp3, defense_effectiveness, accuracy, speed)
            balls_shot2, cycle_time2 = rebounds(same2, opp1, opp2, opp3, defense_effectiveness, accuracy, speed)
            total_balls = max(totalRebounds(balls_shot1, cycle_time1, balls_shot2, cycle_time2),
                              totalRebounds(balls_shot2, cycle_time2, balls_shot1, cycle_time1))
            pct = percentage(me, opp1, opp2, opp3, defense_effectiveness, accuracy)
            scored_balls = math.floor(total_balls * pct)
            if debug: print(f"two shooters, one rebounder [{me}] balls {total_balls} pct {pct}")
            return ballScore(me, scored_balls)
        elif same1.role == 1 and same2.role == 2: # one shooter, another rebounder
            balls_shot1, cycle_time1 = rebounds(same1, opp1, opp2, opp3, defense_effectiveness, accuracy, speed)
            total_balls = balls_shot1 // 2 # share with other rebounder
            pct = percentage(me, opp1, opp2, opp3, defense_effectiveness, accuracy)
            scored_balls = math.floor(total_balls * pct)
            if debug: print(f"one shooter, two rebounders [{me}] balls {total_balls} pct {pct}")
            return ballScore(me, scored_balls)
        elif same1.role == 2 and same2.role == 1: # one shooter, another rebounder
            balls_shot2, cycle_time2 = rebounds(same2, opp1, opp2, opp3, defense_effectiveness, accuracy, speed)
            total_balls = balls_shot2 // 2 # share with other rebounder
            pct = percentage(me, opp1, opp2, opp3, defense_effectiveness, accuracy)
            scored_balls = math.floor(total_balls * pct)
            if debug: print(f"one shooter, two rebounders [{me}] balls {total_balls} pct {pct}")
            return ballScore(me, scored_balls)
        elif same1.role == 1: # one shooter
            balls_shot1, cycle_time1 = rebounds(same1, opp1, opp2, opp3, defense_effectiveness, accuracy, speed)
            total_balls = balls_shot1
            pct = percentage(me, opp1, opp2, opp3, defense_effectiveness, accuracy)
            scored_balls = math.floor(total_balls * pct)
            if debug: print(f"one shooter one rebounder [{me}] balls {total_balls} pct {pct}")
            return ballScore(me, scored_balls)
        elif same2.role == 1: # one shooter
            balls_shot2, cycle_time2 = rebounds(same2, opp1, opp2, opp3, defense_effectiveness, accuracy, speed)
            total_balls = balls_shot2
            pct = percentage(me, opp1, opp2, opp3, defense_effectiveness, accuracy)
            scored_balls = math.floor(total_balls * pct)
            if debug: print(f"one shooter one rebounder [{me}] balls {total_balls} pct {pct}")
            return ballScore(me, scored_balls)
        else:
            return 0 # no shooters

    elif me.role == 3:
        return 0
    elif  me.role == 4:
        return 0

def score(config, defense_effectiveness, accuracy, speed, debug=False):
    red1 = config[0]
    red2 = config[1]
    red3 = config[2]
    blue1 = config[3]
    blue2 = config[4]
    blue3 = config[5]
    red = (scoreImpl(red1, red2, red3, blue1, blue2, blue3, defense_effectiveness, accuracy, speed, debug)
         + scoreImpl(red2, red1, red3, blue1, blue2, blue3, defense_effectiveness, accuracy, speed, debug)
         + scoreImpl(red3, red1, red2, blue1, blue2, blue3, defense_effectiveness, accuracy, speed, debug))
    if debug:
        print(f"red {red}")
        print(red1)
        print(red2)
        print(red3)
    blue = (scoreImpl(blue1, blue2, blue3, red1, red2, red3, defense_effectiveness, accuracy, speed, debug)
         + scoreImpl(blue2, blue1, blue3, red1, red2, red3, defense_effectiveness, accuracy, speed, debug)
         + scoreImpl(blue3, blue1, blue2, red1, red2, red3, defense_effectiveness, accuracy, speed, debug))
    if debug:
        print(f"blue {blue}")
        print(blue1)
        print(blue2)
        print(blue3)
    return [red,blue]

def perturb(c, alliance): # 1 is red, 2 is blue
    cc = copy.deepcopy(c)
    ci = randint(0,2) if alliance == 1 else randint(3,5)
    cc[ci] = randAgent()
    return cc

def findBest(defense_effectiveness, accuracy, speed):
    high_score_sum = 0
    best_c = None
    best_r = 0
    best_b = 0
    for i in range(0,5):
        c = [randAgent(), randAgent(), randAgent(), randAgent(), randAgent(), randAgent()]
        for p in range(0,6000):
            r, b = score(c, defense_effectiveness, accuracy, speed)
            alliance = randint(1,2) # perturb one team's strategy
            pc = perturb(c, alliance)
            pcr, pcb = score(pc, defense_effectiveness, accuracy, speed)
            base_score_diff = (r - b) if alliance == 1 else (b - r)
            new_score_diff = (pcr - pcb) if alliance == 1 else (pcb - pcr)
            if (new_score_diff > base_score_diff):
                #print (f'improve {p} alliance: {alliance} r {r} b {b} pcr {pcr} pcb {pcb}')
                c = pc
        if False:
            print("")
            print("iter %d" % i)
        r, b = score(c, defense_effectiveness, accuracy, speed)
        if r+b > high_score_sum:
            best_c = c
            best_r = r
            best_b = b
    return best_c, best_r, best_b


# random initialization, then greedy
def main():
    for defense_effectiveness in [1.25, 1.75]:
        for accuracy in [0.8, 0.5]:
            for speed in [5, 10]:  # time to traverse field from one end to the other
                best_c, best_r, best_b = findBest(defense_effectiveness, accuracy, speed)
                print(f"defense_effectiveness {defense_effectiveness} accuracy {accuracy} speed {speed}")
                print(f"red {best_r}")
                print(best_c[0])
                print(best_c[1])
                print(best_c[2])
                print(f"blue {best_b}")
                print(best_c[3])
                print(best_c[4])
                print(best_c[5])
        

if __name__ == '__main__':
    main()
