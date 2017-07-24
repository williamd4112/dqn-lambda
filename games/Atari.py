from AgentGround import AgentGround
import numpy as np
import gym


class Atari:
	def __init__(self, cfg_parser, sess):
		self.cfg_parser = cfg_parser

		self.env_name = 'Pong-ram-v0'
		self.env = gym.make(self.env_name)
		self.obs = self.env.reset()

		# TODO 2017 make this a parameter/handled automatically in the game
		self.gamma = 0.95

		# Init agents/evader
		self.init_agt(sess=sess)

		# Initialize agent NNs (need the game initialized at this point, since will need things like observation dimensions well-defined)
		self.create_agt_nn(sess=sess)

		# Reset game (and also RNN state when applicable)
		self.reset_game()

	def create_agt_nn(self, sess):
		# Create actual player NNs
		self.agt.create_nns(cfg_parser=self.cfg_parser, sess=sess, scope_suffix='', env_s_0=self.obs, parameter_sharing=False)

	def init_agt_nnT(self):
		# Placed here since must be run after tf.all_variables_initialized()
		self.agt.init_nnT()

	def init_agt(self, sess):
		# Init agents
		self.agt = AgentGround(player_type='agent', cfg_parser=self.cfg_parser, i_agt=0, n_agts=1, xy_0=[0,0], x_lim=[-1,1], y_lim=[-1,1], is_toroidal=False, sess=sess)

	def reset_game(self):
		self.discount = 1.0
		self.value = 0.0
		self.next_joint_o = None # Store the observation to ensure consistency in noise/observation process when querying observations within same timestep

		self.env.reset()

		# Reset RNN state (does nothing for non-RNN case)
		self.agt.reset_rnn_state()

	def get_joint_obs(self):
		# Observations are pre-processed at the previous timestep (in self.next()) due to
		# POMDP-ness (to ensure multiple queried observations at same timestep don't change due to noise)
		if self.next_joint_o is None:
			# First game timestep, so no preprocessed next_joint_o yet, grab a fresh one
			return [self.obs]
		else:
			# Get pre-processed observation
			return self.next_joint_o

	def next(self, i_actions):
		if len(i_actions) != 1:
			raise ValueError('Incorrect number of actions specified! 1 agent needs exactly 1 action!')

		# Agents execute actions
		action = np.argmax(i_actions)
		next_obs, r, game_over, info = self.env.step(action)

		self.env.render()

		# Save rewards for agents (in case they want to include as part of state)
		self.agt.last_reward = r

		# Pack next joint state
		self.next_joint_o = [next_obs]

		# Accrue value
		self.value += self.discount*r
		self.discount *= self.gamma
		value_so_far = self.value # Must be here due to resetting logic below
		next_joint_o_latest = self.next_joint_o # Must be here due to resetting logic below

		if game_over:
			print '-------------- Total episode reward', value_so_far, '!--------------'
			self.reset_game()

		return next_joint_o_latest, r, game_over, value_so_far
