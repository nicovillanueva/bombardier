import socket
import poormanslogging as log

LISTENPORT = 6666

class Grunt(object):
	def __init__(self):
		try:
			self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.s.bind(('', LISTENPORT))
			self.s.listen(1)
			log.info('Waiting for orders on port {}'.format(LISTENPORT))
			(c, a) = self.s.accept()
			self._receive_orders(c)
		finally:
			log.info('Shutting down')
			self.s.close()


	def _receive_orders(self, sock):
		chunks = []
		while 1:
			try:
				chunks.append(self.s.recv(1024))
			except OSError:
				break
		msg = b''.join(chunks)
		print("Message:")
		print(msg)
