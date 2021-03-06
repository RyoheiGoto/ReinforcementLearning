import numpy as np
from plot import Penplot

##############################################
cart_mass = 0.5
pole_mass = 0.1
pole_length = 0.25
pole_masslength = pole_mass * pole_length
total_mass = cart_mass + pole_mass

gravity = 9.8
force_mag = 4.5
tau = 0.02

four_thirds = 1.3333333333333

one_degrees = 0.0174532
six_degrees = 0.1047192
twelve_degrees = 0.2094384
eighteen_degrees = 0.3141592653589793
fifty_degrees = 0.87266

epsilon = 0.1
gamma = 0.4
##############################################

class Pendulum(object):
    def __init__(self):
        print "-" * 30
        np.random.seed()
        self.Q = np.zeros([2, 3, 3, 6, 3])
        self.D = None
        self.d = None
        self.s = None

    def _update_status(self, old_states, action):
        x, x_dot, theta, theta_dot = old_states
        
        force = force_mag if action > 0 else -force_mag
        cos_theta = np.cos(theta)
        sin_theta = np.sin(theta)
        
        temp = (force + pole_masslength * theta_dot**2 * sin_theta) / total_mass
        theta_acc = (gravity * sin_theta - cos_theta * temp) /\
                    (pole_length * (four_thirds - pole_mass * cos_theta**2 / total_mass))
        x_acc = temp - pole_masslength * theta_acc * cos_theta / total_mass
        
        x += tau * x_dot
        x_dot += tau * x_acc
        theta += tau * theta_dot
        theta_dot += tau * theta_acc
        
        return x, x_dot, theta, theta_dot

    def _e_greedy(self, states, act=2):
        policy = []
        x, x_dot, theta, theta_dot = self._threshold(states)
        quantity = [self.Q[action, x, x_dot, theta, theta_dot] for action in xrange(act)]
        
        for action in quantity:
            if action == max(quantity):
                policy.append(1.0 - epsilon + epsilon / act)
            else:
                policy.append(epsilon / act)
        
        if sum(policy) == 1.0:
            return policy
        else:
            return map(lambda n: 1.0 / act, policy)

    def _decide_action(self, policy):
        prob = 0.0
        for action in xrange(len(policy)):
            prob += policy[action]
            if np.random.random() < prob:
                return action
    
    def _get_reward(self, states):
        x, x_dot, theta, theta_dot = [np.fabs(state) for state in states]
        
        if x > 2.4 or theta > twelve_degrees:
            return 0.0
        else:
            return 1.0

    def _threshold(self, states):
        x, x_dot, theta, theta_dot = states
        
        if x < -0.8:
            s1 = 0
        elif x < 0.8:
            s1 = 1
        else:
            s1 = 2
        
        if x_dot < -0.5:
            s2 = 0
        elif x_dot < 0.5:
            s2 = 1
        else:
            s2 = 2
        
        if theta < -six_degrees:
            s3 = 0
        elif theta < -one_degrees:
            s3 = 1
        elif theta < 0.0:
            s3 = 2
        elif theta < one_degrees:
            s3 = 3
        elif theta < six_degrees:
            s3 = 4
        else:
            s3 = 5
        
        if theta_dot < -fifty_degrees:
            s4 = 0
        elif theta_dot < fifty_degrees:
            s4 = 1
        else:
            s4 = 2
        
        return s1, s2, s3, s4

    def _step(self):
        states = self.s
        policy = self._e_greedy(states)
        action = self._decide_action(policy)
        
        new_states = self._update_status(states, action)
        reward = self._get_reward(new_states)
        
        self.s = new_states
        self.d.append((states, action, reward, new_states))
        
        return False if reward < 1.0 else True

    def _mc(self):
        self.Q = np.zeros_like(self.Q)
        num = np.zeros_like(self.Q)
        
        for m in self.D:
            for t in xrange(len(m)):
                d = m[t:]
                q = 0.0

                for current in xrange(len(d)):
                    q += gamma ** current * d[current][2]

                states, action, reward, new_states = m[t]
                x, x_dot, theta, theta_dot = self._threshold(states)
                self.Q[action, x, x_dot, theta, theta_dot] += q
                num[action, x, x_dot, theta, theta_dot] += 1.0
        
        num[num == 0.0] = 1.0
        self.Q /= num

    def process(self, max_episode=1000, update=True, plot=False, save=None):
        self.D = []
        total_steps = 0
        max_step = 0
        state_list = None
        
        for episode in np.arange(0, max_episode):
            self.d = []
            self.s = (0, 0, 0, 0)
            for step in np.arange(0, 100000):
                if not self._step():
                    self.D.append(self.d)
                    total_steps += step
                    max_step = max(max_step, step)
                    if max_step is step:
                        state_list = self.d
                    break
            else:
                print "episode %d is complite %d steps" % (episode, 100000)
        
        print "Episode:\t%d" % max_episode
        print "Average:\t%d (%.2lfs)" % (total_steps / max_episode, (total_steps / max_episode) * tau)
        print "Max step:\t%d (%.2lfs)" % (max_step, max_step * tau)
        
        if plot and state_list:
            state = [d[0] for d in state_list]
            Penplot(state, anime=True, fig=True)
        if update:
            self._mc()
        if save and state_list:
            q, s = save.split(" ")
            states = [d[0] for d in state_list]
            np.save(q, self.Q)
            np.save(s, states)
        print "-" * 30

if __name__ == '__main__':
    pendulum = Pendulum()
    pendulum.process(10000, plot=True)
    pendulum.process(10000, plot=True)
    pendulum.process(10000, update=False, plot=True, save="Q.npy states.npy")

