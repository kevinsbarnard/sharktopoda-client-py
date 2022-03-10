import zmq
import time
from threading import Thread, current_thread
from queue import Empty, Queue

from sharktopoda_client.JavaTypes import randomString
from sharktopoda_client.Log import get_logger
from sharktopoda_client.localization.Message import Message
from sharktopoda_client.localization.LocalizationController import LocalizationController
from sharktopoda_client.localization.SelectionController import SelectionController


class IO:

    def __init__(
        self,
        incomingPort: int,
        outgoingPort: int,
        incomingTopic: str,
        outgoingTopic: str,
        controller: LocalizationController = None,
    ) -> None:
        self.ok: bool = True
        self.log = get_logger('IO')
        
        self.context = zmq.Context()
        self.incomingPort = incomingPort
        self.outgoingPort = outgoingPort
        
        self.queue = Queue()
        self.sourceId = randomString(10)
        
        if controller is None:
            controller = LocalizationController()
        self.controller = controller
        self.controller.getOutgoing().subscribe(lambda l: self.queue.put(l))
        self.selectionController = SelectionController(self.controller)
        
        def outgoing():
            address = 'tcp://*:' + str(outgoingPort)
            self.log.info('ZeroMQ publishing to {} using topic \'{}\''.format(address, outgoingTopic))
            publisher = self.context.socket(zmq.PUB)
            publisher.bind(address)
            
            thread = current_thread()
            try:
                time.sleep(1)
            except InterruptedError as e:
                self.log.warn('ZeroMQ publisher thread was interrupted', e)
            
            while self.ok and thread.is_alive():
                try:
                    msg = self.queue.get(timeout=1)
                    if msg is not None:
                        json_str = msg.to_json()
                        self.log.debug('Publishing message to \'{}\': {}'.format(outgoingTopic, json_str))
                        publisher.send_string(outgoingTopic, flags=zmq.SNDMORE)
                        publisher.send_string(json_str)
                except Empty:
                    pass
                except InterruptedError as e:
                    self.log.warn('ZeroMQ publisher thread was interrupted', e)
                    self.ok = False
                except Exception as e:
                    self.log.warn(f'An exception was thrown while attempting to publish a localization: {e}')
            
            self.log.info('Shutting down ZeroMQ publisher thread at {}'.format(address))
            publisher.close()
        
        self.outgoingThread = Thread(target=outgoing, daemon=True)
        self.outgoingThread.start()
        
        def incoming():
            address = 'tcp://localhost:' + str(incomingPort)
            self.log.info('ZeroMQ subscribing to {} using topic \'{}\''.format(address, incomingTopic))
            socket = self.context.socket(zmq.SUB)
            socket.connect(address)
            socket.subscribe(incomingTopic.encode('utf-8'))
            
            thread = current_thread()
            while self.ok and thread.is_alive():
                try:
                    topicAddress = socket.recv_string()
                    contents = socket.recv_string()
                    message = Message.from_json(contents)
                    controller.getIncoming().on_next(message)
                except zmq.ZMQError as e:
                    if e.errno == 156384765:
                        pass
                    else:
                        self.log.warn('An exception occurred while reading from remote app', e)
                except Exception as e:
                    self.log.warn('An exception occurred while reading from remote app', e)
        
        self.incomingThread = Thread(target=incoming, daemon=True)
        self.incomingThread.start()

    def publish(self, message: Message):
        self.controller.getOutgoing().on_next(message)
    
    def close(self):
        self.ok = False
        self.context.destroy()
        self.controller.getIncoming().on_completed()
        self.controller.getOutgoing().on_completed()
