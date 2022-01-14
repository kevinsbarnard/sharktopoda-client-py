import zmq
import time
import json
import datetime
from logging import Logger
from typing import Any
from threading import Thread, current_thread
from queue import Queue

from sharktopoda_client.JavaTypes import Duration, randomString
from sharktopoda_client.gson.DurationConverter import DurationConverter
from sharktopoda_client.localization.Message import Message
from sharktopoda_client.localization.LocalizationController import LocalizationController


class IO:
    class MessageEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, datetime.datetime):
                return o.strftime('%Y-%m-%dT%H:%M:%SZ')
            elif isinstance(o, Duration):
                return DurationConverter.serialize(o.toMillis())
            else:
                return json.JSONEncoder.default(self, o)
    
    gson = MessageEncoder()

    def __init__(
        self,
        incomingPort: int,
        outgoingPort: int,
        incomingTopic: str,
        outgoingTopic: str,
        controller: LocalizationController = None,
    ) -> None:
        self.ok: bool = True
        self.log = Logger('IO')
        
        self.context = zmq.Context()
        self.incomingPort = incomingPort
        self.outgoingPort = outgoingPort
        
        self.queue = Queue()
        self.sourceId = randomString(10)
        
        if controller is None:
            controller = LocalizationController()
        self.controller = controller
        # self.controller.getOutgoing().ofType(Message.class).subscribe(lcl -> queue.offer(lcl))
        # self.selectionController = controller.copy()
        
        def outgoing():
            address = 'tcp://*:' + str(outgoingPort)
            self.log.info('ZeroMQ publishing to {} using topic \'{}\''.format(address, outgoingTopic))
            publisher = self.context.socket(zmq.PUB)
            publisher.bind(address)
            
            thread = current_thread()
            try:
                time.sleep(1000)
            except InterruptedError as e:
                self.log.warn('ZeroMQ publisher thread was interrupted', e)
            
            while self.ok and thread.is_alive():
                try:
                    msg = self.queue.get(timeout=1)
                    if msg is not None:
                        json_str = self.gson.toJson(msg)
                        self.log.debug('Publishing message to \'{}\': \n{}'.format(outgoingTopic, json_str))
                        publisher.send_string(outgoingTopic, flags=zmq.SNDMORE)
                        publisher.send_json(msg, encoder=IO.gson)
                except InterruptedError as e:
                    self.log.warn('ZeroMQ publisher thread was interrupted', e)
                    self.ok = False
                except Exception as e:
                    self.log.warn('An exception was thrown while attempting to publish a localization', e)
            
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
                    # controller.getIncoming().onNext(message)
                except zmq.ZMQError as e:
                    if e.errno == 156384765:
                        pass
                    else:
                        self.log.warn('An exception occurred while reading from remote app', e)
                except Exception as e:
                    self.log.warn('An exception occurred while reading from remote app', e)
        
        self.incomingThread = Thread(target=incoming, daemon=True)
        self.incomingThread.start()
