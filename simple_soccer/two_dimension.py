import numpy as np
import matplotlib.pyplot as plt

field_width = 396
field_hight = 180
goal_length = 180

threshold = 36
field_width_threshold_num = field_width / threshold + 1
field_width_threshold = [Y * threshold - field_width / 2.0 for Y in xrange(field_width_threshold_num)]
field_hight_threshold_num = field_hight / threshold + 1
field_hight_threshold = [X * threshold for X in xrange(field_hight_threshold_num)]

ball_velo_x_threshold = [X * 100.0 for X in [-1.0, -0.8, -0.6, -0.4, -0.2, 0.0]]
ball_velo_x_threshold_num = len(ball_velo_x_threshold) + 1
ball_velo_y_threshold = [Y * 10.0 for Y in [-1.0, -0.8, -0.6, -0.4, -0.2, 0.0, 0.2, 0.4, 0.6, 0.8, 1.0]]
ball_velo_y_threshold_num = len(ball_velo_y_threshold) + 1

tau = 0.2
fall_time = 5.0
robot_states = 3

epsilon = 0.1
alpha = 0.4
gamma = 0.4

COMPLETED, FAILED, ACTIVE = range(3)
STAND, LEFT, RIGHT, BALL = range(4)


class Soccer(object):
    def __init__(self, max_episode=10000, plot=False):
        np.random.seed()
        self.Q = np.zeros([robot_states, field_hight_threshold_num, field_width_threshold_num, ball_velo_x_threshold_num, ball_velo_y_threshold_num])
        self.robot_state = None
        self.fall_count = None
        self.ball_states = None
        self.result = None

        self.process(max_episode, plot)

    def status_init(self):
        ball_x = np.random.randint(100, 170)
        ball_y = np.random.randint(-60, 60)
        ball_dx = -np.random.random() * 100
        ball_dy = np.random.choice([10, -10]) * np.random.random()

        self.ball_states = (ball_x, ball_y, ball_dx, ball_dy)
        self.robot_state = STAND

    def threslold(self, states):
        x, y, dx, dy = states

        for field_x, num in zip(field_hight_threshold, xrange(field_hight_threshold_num)):
            if x < field_x:
                threshold_x = num
                break
        else:
            threshold_x = field_hight_threshold_num - 1

        for field_y, num in zip(field_width_threshold, xrange(field_width_threshold_num)):
            if y < field_y:
                threshold_y = num
                break
        else:
            threshold_y = field_width_threshold_num - 1

        for ball_dx, num in zip(ball_velo_x_threshold, xrange(ball_velo_x_threshold_num)):
            if dx < ball_dx:
                threshold_dx = num
                break
        else:
            threshold_dx = ball_velo_x_threshold_num - 1

        for ball_dy, num in zip(ball_velo_y_threshold, xrange(ball_velo_y_threshold_num)):
            if dy < ball_dy:
                threshold_dy = num
                break
        else:
            threshold_dy = ball_velo_y_threshold_num - 1

        return threshold_x, threshold_y, threshold_dx, threshold_dy

    def update_status(self, ball_states):
        ball_x, ball_y, ball_dx, ball_dy = ball_states

        ball_x += ball_dx * tau
        ball_y += ball_dy * tau

        self.ball_states = [ball_x, ball_y, ball_dx, ball_dy]

    def decide_action(self, ball_states, robot_state):
        if robot_state == (LEFT or RIGHT):
            self.fall_count -= 1
        else:
            policy = self.e_greedy(ball_states)
            prob = 0.0
            for action, policy in zip(xrange(robot_states), policy):
                prob += policy
                if np.random.random() < prob:
                    self.robot_state = action
                    if action == (LEFT or RIGHT):
                        self.fall_count = fall_time
                    break
            else:
                self.robot_state = STAND

    def e_greedy(self, ball_states):
        policy = []
        x, y, dx, dy = self.threslold(ball_states)
        q = [self.Q[action, x, y, dx, dy] for action in xrange(robot_states)]

        for action in xrange(len(q)):
            if action == q.index(max(q)):
                policy.append(1.0 - epsilon + epsilon / robot_states)
            else:
                policy.append(epsilon / robot_states)

        if sum(policy) != 1.0 or not sum(q):
            return map(lambda n: 1.0 / robot_states, policy)
        else:
            return policy

    def get_reward(self, ball_states, robot_state):
        x, y, dx, dy = self.threslold(ball_states)
        reward = 0.0
        result = ACTIVE

        if robot_state == STAND:
            if x == 1 and y == 6:
                reward = 5.0
                result = COMPLETED
            else:
                reward = 1.0
        elif robot_state == LEFT:
            if x == 1 and y in (4, 5):
                reward = 5.0
                result = COMPLETED
            elif not self.fall_count > 0:
                reward = -5.0
                result = FAILED
            else:
                reward = -5.0
        elif robot_state == RIGHT:
            if x == 1 and y in (7, 8):
                reward = 1.0
                result = COMPLETED
            elif not self.fall_count > 0:
                reward = -5.0
                result = FAILED
            else:
                reward = -5.0

        if x == 0 and (3 < y < 9):
            reward = -10.0
            result = FAILED
        elif x in (0, 6) and (y < 4 or y > 8):
            reward = 1.0
            result = COMPLETED

        return reward, result

    def q_learning(self, ball_states, new_ball_states, new_robot_state, reward):
        x, y, dx, dy = self.threslold(new_ball_states)
        new = max([self.Q[action, x, y, dx, dy] for action in xrange(robot_states)])

        x, y, dx, dy = self.threslold(ball_states)
        old = self.Q[new_robot_state, x, y, dx, dy]

        self.Q[new_robot_state, x, y, dx, dy] += alpha * (reward + gamma * new - old)

    def step(self):
        ball_states = self.ball_states
        robot_state = self.robot_state

        self.decide_action(ball_states, robot_state)

        self.update_status(ball_states)
        new_ball_states = self.ball_states
        new_robot_states = self.robot_state

        reward, result = self.get_reward(new_ball_states, new_robot_states)
        self.q_learning(ball_states, new_ball_states, new_robot_states, reward)

        if result == ACTIVE:
            return True
        else:
            self.result = result
            return False

    def process(self, max_episode, plot):
        clear = 0.0

        for episode in np.arange(1, max_episode):
            self.status_init()
            log = []
            for step in np.arange(1, 10000):
                ball_x, ball_y, ball_dx, ball_dy = self.ball_states
                log.append([step * tau, ball_x, ball_y, ball_dx, ball_dy, self.robot_state])
                if not self.step():
                    ball_x, ball_y, ball_dx, ball_dy = self.ball_states
                    log.append([step * tau, ball_x, ball_y, ball_dx, ball_dy, self.robot_state])
                    if self.result == COMPLETED:
                        clear += 1.0
                    if plot and episode > max_episode / 2:
                        self.plotgame(log, self.result)
                    break

        print "episode: %lf\nclear: %lf(%lf%%)" % (max_episode, clear, (clear / max_episode) * 100)

    def plotgame(self, episode, result):
        field = np.zeros([field_hight_threshold_num, field_width_threshold_num])
        for step in episode:
            time, ball_x, ball_y, ball_dx, ball_dy, robot_state = step
            x, y, dx, dy = self.threslold([ball_x, ball_y, ball_dx, ball_dy])

            field[x, y] = BALL
            if robot_state == STAND:
                field[0, 6] = 10
            elif robot_state == LEFT:
                field[0, 4] = field[0, 5] = 20
            elif robot_state == RIGHT:
                field[0, 7] = field[0, 8] = 30

        if result == COMPLETED:
            result = "CLEAR"
        else:
            result = "FAILED"

        plt.clf()
        plt.imshow(field, interpolation='none')
        plt.title(r"%s" % result)
        plt.show()

if __name__ == '__main__':
    #Soccer(plot=True)
    Soccer()

