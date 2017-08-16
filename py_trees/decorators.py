#!/usr/bin/env python
#
# License: BSD
#   https://raw.githubusercontent.com/stonier/py_trees/devel/LICENSE
#
##############################################################################
# Documentation
##############################################################################
"""
Meta done in composite way
"""

##############################################################################
# Imports
##############################################################################

import time

from .composites import Composite
from .common import Status


##############################################################################
# Decorator Composites
##############################################################################

class Decorator(Composite):
    def __init__(self, child, name="Decorator", *args, **kwargs):
        # make sure the child is there and one
        super(Decorator, self).__init__(name=name, children=[child], *args, **kwargs)
        # There will only be one child
        self.current_child = child

    def tick(self):
        self.logger.debug("%s.tick()" % self.__class__.__name__)

        if self.status != Status.RUNNING:
            self.initialise()

        # from here we just need to tick the child and patch with this
        # meta's update
        for node in self.current_child.tick():
            if node != self.current_child:
                yield node
        new_status = self.update()
        if new_status not in list(Status):
            self.logger.error("A behaviour returned an invalid status, setting to INVALID [%s][%s]"
                              % (new_status, self.name))
            new_status = Status.INVALID
        self.status = new_status
        yield self

    def update(self):
        """
        This is the usual method that gets replaced by
        the meta classes.
        """
        return self.current_child.status

    def __repr__(self):
        """
        Simple string representation of the object.

        Returns:
            :obj:`str`: string representation
        """
        s = "Name       : %s\n" % self.name
        s += "  Status  : %s\n" % self.status
        s += "  Child : %s\n" % (self.current_child.name if self.current_child is not None else "none")
        s += "  Child Status: %s\n" % self.current_child.status
        return s


#############################
# SuccessIsFailure
#############################

class SuccessIsFailure(Decorator):
    def __init__(self, child, name="SuccessIsFailure", *args, **kwargs):
        super(SuccessIsFailure, self).__init__(child, name=name, *args, **kwargs)

    def update(self):
        if self.current_child.status == Status.SUCCESS:
            self.feedback_message = "success is failure" + (" [%s]" % self.current_child.feedback_message
                                                            if self.current_child.feedback_message else "")
            return Status.FAILURE
        else:
            self.feedback_message = self.current_child.feedback_message
            return self.current_child.status


#############################
# SuccessIsRunning
#############################

class SuccessIsRunning(Decorator):
    def __init__(self, child, name="SuccessIsRunning", *args, **kwargs):
        super(SuccessIsRunning, self).__init__(child, name=name, *args, **kwargs)

    def update(self):
        if self.current_child.status == Status.SUCCESS:
            self.feedback_message = "success is running [%s]" % self.current_child.feedback_message
            return Status.RUNNING
        else:
            self.feedback_message = self.current_child.feedback_message
            return self.current_child.status


#############################
# RunningIsSuccess
#############################

class RunningIsSuccess(Decorator):
    def __init__(self, child, name="RunningIsSuccess", *args, **kwargs):
        super(RunningIsSuccess, self).__init__(child, name=name, *args, **kwargs)

    def update(self):
        if self.current_child.status == Status.RUNNING:
            self.feedback_message = "running is success" + (" [%s]" % self.current_child.feedback_message
                                                            if self.current_child.feedback_message else "")
            return Status.SUCCESS
        else:
            self.feedback_message = self.current_child.feedback_message
            return self.current_child.status


#############################
# RunningIsFailure
#############################

class RunningIsFailure(Decorator):
    def __init__(self, child, name="RunningIsFailure", *args, **kwargs):
        super(RunningIsFailure, self).__init__(child, name=name, *args, **kwargs)

    def update(self):
        if self.current_child.status == Status.RUNNING:
            self.feedback_message = "running is failure" + (" [%s]" % self.current_child.feedback_message
                                                            if self.current_child.feedback_message else "")
            return Status.FAILURE
        else:
            self.feedback_message = self.current_child.feedback_message
            return self.current_child.status


#############################
# FailureIsSuccess
#############################


class FailureIsSuccess(Decorator):
    def __init__(self, child, name="FailureIsSuccess", *args, **kwargs):
        super(FailureIsSuccess, self).__init__(child, name=name, *args, **kwargs)

    def update(self):
        if self.current_child.status == Status.FAILURE:
            self.feedback_message = "failure is success" + (" [%s]" % self.current_child.feedback_message
                                                            if self.current_child.feedback_message else "")
            return Status.SUCCESS
        else:
            self.feedback_message = self.current_child.feedback_message
            return self.current_child.status


#############################
# FailureIsRunning
#############################

class FailureIsRunning(Decorator):
    def __init__(self, child, name="FailureIsRunning", *args, **kwargs):
        super(FailureIsRunning, self).__init__(child, name=name, *args, **kwargs)

    def update(self):
        if self.current_child.status == Status.FAILURE:
            self.feedback_message = "failure is running" + (" [%s]" % self.current_child.feedback_message
                                                            if self.current_child.feedback_message else "")
            return Status.RUNNING
        else:
            self.feedback_message = self.current_child.feedback_message
            return self.current_child.status

##############################################################################
# Inverter
##############################################################################


class Inverter(Decorator):
    def __init__(self, child, name="Inverter", *args, **kwargs):
        super(Inverter, self).__init__(child, name=name, *args, **kwargs)

    def update(self):
        if self.current_child.status == Status.SUCCESS:
            return Status.FAILURE
            self.feedback_message = "success -> failure"
        elif self.current_child.status == Status.FAILURE:
            self.feedback_message = "failure -> success"
            return Status.SUCCESS
        else:
            self.feedback_message = self.current_child.feedback_message
            return self.current_child.status


#############################
# Condition
#############################

class Condition(Decorator):
    def __init__(self, child, status, name="Condition", *args, **kwargs):
        super(Condition, self).__init__(child, name=name, *args, **kwargs)
        self.succeed_status = status

    def update(self):
        self.logger.debug("%s.update()" % self.__class__.__name__)
        self.feedback_message = "'{0}' has status {1}, waiting for {2}".format(self.current_child.name,
                                                                               self.current_child.status,
                                                                               self.succeed_status)
        if self.current_child.status == self.succeed_status:
            if self.current_child.status == Status.RUNNING:
                self.current_child.stop()
            return Status.SUCCESS
        else:
            return Status.RUNNING


# ##############################################################################
# # Timeout
# ##############################################################################


class Timeout(Decorator):
    def __init__(self, child, duration, name="Timeout", *args, **kwargs):
        super(Timeout, self).__init__(child, name=name, *args, **kwargs)
        self.duration = duration
        self.finish_time = None

    def initialise(self):
        self.logger.debug("%s.initialise()" % self.__class__.__name__)
        if self.finish_time is None:
            self.finish_time = time.time() + self.duration

    def update(self):
        self.logger.debug("%s.update()" % self.__class__.__name__)
        if self.current_child.status != Status.RUNNING:
            self.initialise()
        current_time = time.time()
        if current_time > self.finish_time:
            self.feedback_message = "timed out"
            # invalidate the current_child (i.e. cancel it)
            self.current_child.stop(Status.INVALID)
            return Status.FAILURE
        else:
            self.feedback_message = self.current_child.feedback_message + \
                                    " [time left: %s]" % (self.finish_time - current_time)
            return self.current_child.status

    def terminate(self, new_status):
        self.logger.debug("%s.terminate()" % self.__class__.__name__)
        if new_status != Status.RUNNING:
            self.finish_time = None


##############################################################################
# Oneshot
##############################################################################

class Oneshot(Decorator):
    def __init__(self, child, name="Oneshot", *args, **kwargs):
        super(Oneshot, self).__init__(child, name=name, *args, **kwargs)

    def tick(self):
        self.logger.debug("%s.tick()" % self.__class__.__name__)

        if self.status != Status.RUNNING:
            self.initialise()

        # from here we just need to tick the child and patch with this
        # meta's update
        if self.current_child.status == Status.FAILURE or self.current_child.status == Status.SUCCESS:
            # if returned success/fail at any point, don't update or re-init
            yield self
        else:
            for node in self.current_child.tick():
                if node != self.current_child:
                    yield node
            new_status = self.update()
            if new_status not in list(Status):
                self.logger.error("A behaviour returned an invalid status, setting to INVALID [%s][%s]"
                                  % (new_status, self.name))
                new_status = Status.INVALID
            self.status = new_status
            yield self
