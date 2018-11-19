import tensorflow as tf


class Discriminator:
    def __init__(self, state_dim, action_count, hidden_size=128, tf_session=None, scope_name="default"):
        if tf_session is None:
            session_config = tf.ConfigProto(device_count={'GPU': 1})
            session_config.gpu_options.visible_device_list = str('0')
            session_config.gpu_options.allow_growth = True
            self.sess = tf.Session(config=session_config)
        else:
            self.sess = tf_session

        self.scope_name = scope_name
        self.hidden_size = hidden_size

        with tf.variable_scope(self.scope_name):
            self.expert_s = tf.placeholder(dtype=tf.float32, shape=[None, state_dim])
            self.expert_a = tf.placeholder(dtype=tf.int32, shape=[None])
            expert_a_one_hot = tf.one_hot(self.expert_a, depth=action_count)
            expert_s_a = tf.concat([self.expert_s, expert_a_one_hot], axis=1)

            self.agent_s = tf.placeholder(dtype=tf.float32, shape=[None, state_dim])
            self.agent_a = tf.placeholder(dtype=tf.int32, shape=[None])
            agent_a_one_hot = tf.one_hot(self.agent_a, depth=action_count)
            agent_s_a = tf.concat([self.agent_s, agent_a_one_hot], axis=1)

            with tf.variable_scope('d_network') as network_scope:
                prob_1 = self.construct_network(input=expert_s_a)
                network_scope.reuse_variables()  # share parameter
                prob_2 = self.construct_network(input=agent_s_a)

            with tf.variable_scope('d_loss'):
                loss_expert = tf.reduce_mean(tf.log(tf.clip_by_value(1-prob_1, 0.01, 1)))
                loss_agent = tf.reduce_mean(tf.log(tf.clip_by_value(prob_2, 0.01, 1)))
                loss = loss_expert + loss_agent
                loss = -loss

            optimizer = tf.train.AdamOptimizer()
            self.train_op = optimizer.minimize(loss)

        # self.rewards = tf.log(tf.clip_by_value(prob_2, 1e-1, 10))
        # self.rewards = -tf.log(tf.clip_by_value(prob_2, 1e-2, 1))
        self.rewards = 1-prob_2

        if tf_session is None:
            self.sess.run(tf.global_variables_initializer())
            self.saver = tf.train.Saver(max_to_keep=0)

    def construct_network(self, input):
        layer_1 = tf.layers.dense(inputs=input, units=self.hidden_size, activation=tf.nn.leaky_relu, name='layer1') #tf.nn.leaky_relu
        layer_2 = tf.layers.dense(inputs=layer_1, units=self.hidden_size, activation=tf.nn.leaky_relu, name='layer2')
        layer_3 = tf.layers.dense(inputs=layer_2, units=self.hidden_size, activation=tf.nn.leaky_relu, name='layer3')
        prob = tf.layers.dense(inputs=layer_3, units=1, activation=tf.sigmoid, name='prob')
        return prob

    def train(self, expert_s, expert_a, agent_s, agent_a):
        return self.sess.run(self.train_op, feed_dict={self.expert_s: expert_s,
                                                       self.expert_a: expert_a,
                                                       self.agent_s: agent_s,
                                                       self.agent_a: agent_a})

    def get_rewards(self, agent_s, agent_a):
        return self.sess.run(self.rewards, feed_dict={self.agent_s: agent_s,
                                                      self.agent_a: agent_a})

    def save(self, ckpt_path):
        self.saver.save(self.sess, ckpt_path)
