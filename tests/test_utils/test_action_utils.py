"""
This source file is part of an OSTIS project. For the latest info, see https://github.com/ostis-ai
Distributed under the MIT License
(See an accompanying file LICENSE or a copy at https://opensource.org/licenses/MIT)
"""
import time

from sc_client.client import erase_elements
from sc_client.constants import sc_type
from sc_client.constants.common import ScEventType

from sc_kpm import ScAgent, ScKeynodes, ScModule
from sc_kpm.identifiers import ActionStatus, CommonIdentifiers
from sc_kpm.sc_result import ScResult
from sc_kpm.utils.action_utils import (
    add_action_arguments,
    call_action,
    call_agent,
    check_action_class,
    execute_action,
    execute_agent,
    finish_action_with_status,
    generate_action,
    wait_agent,
)
from sc_kpm.utils.common_utils import (
    check_connector,
    generate_connector,
    generate_node,
    search_element_by_role_relation,
)
from tests.common_tests import BaseTestCase

test_node_idtf = "test_node"


class ScAgentTest(ScAgent):
    def on_event(self, _src, _connector, target_node) -> ScResult:
        self.logger.info(f"Agent's started")
        finish_action_with_status(target_node)
        return ScResult.OK


class ScModuleTest(ScModule):
    def __init__(self):
        super().__init__(
            ScAgentTest(test_node_idtf, ScEventType.AFTER_GENERATE_OUTGOING_ARC),
            ScAgentTest(test_node_idtf, ScEventType.AFTER_GENERATE_INCOMING_ARC),
        )


class TestActionUtils(BaseTestCase):
    def test_validate_action(self):
        action_class_idtf = "test_action_class"
        action_class_node = ScKeynodes.resolve(action_class_idtf, sc_type.CONST_NODE)
        action = ScKeynodes[CommonIdentifiers.ACTION]
        test_node = generate_node(sc_type.CONST_NODE)
        self.assertFalse(check_action_class(action_class_node, test_node))
        self.assertFalse(check_action_class(action_class_idtf, test_node))
        class_connector = generate_connector(sc_type.CONST_PERM_POS_ARC, action_class_node, test_node)
        self.assertFalse(check_action_class(action_class_node, test_node))
        self.assertFalse(check_action_class(action_class_idtf, test_node))
        generate_connector(sc_type.CONST_PERM_POS_ARC, action, test_node)
        self.assertTrue(check_action_class(action_class_node, test_node))
        self.assertTrue(check_action_class(action_class_idtf, test_node))
        erase_elements(class_connector)
        self.assertFalse(check_action_class(action_class_node, test_node))
        self.assertFalse(check_action_class(action_class_idtf, test_node))

    def test_execute_agent(self):
        module = ScModuleTest()
        self.server.add_modules(module)
        with self.server.register_modules():
            assert execute_agent({}, [], test_node_idtf)[1]
        self.server.remove_modules(module)

    def test_call_agent(self):
        module = ScModuleTest()
        self.server.add_modules(module)
        with self.server.register_modules():
            action = call_agent({}, [], test_node_idtf)
            wait_agent(1, action, ScKeynodes[ActionStatus.ACTION_FINISHED])
            result = check_connector(
                sc_type.VAR_PERM_POS_ARC, ScKeynodes[ActionStatus.ACTION_FINISHED_SUCCESSFULLY], action
            )
            self.assertTrue(result)
        self.server.remove_modules(module)

    def test_wrong_execute_agent(self):
        module = ScModuleTest()
        self.server.add_modules(module)
        with self.server.register_modules():
            self.assertFalse(execute_agent({}, [], "wrong_agent", wait_time=1)[1])
        self.server.remove_modules(module)

    def test_execute_action(self):
        module = ScModuleTest()
        self.server.add_modules(module)
        with self.server.register_modules():
            action_node = generate_action()
            add_action_arguments(action_node, {})
            assert execute_action(action_node, test_node_idtf)
        self.server.remove_modules(module)

    def test_call_action(self):
        module = ScModuleTest()
        self.server.add_modules(module)
        with self.server.register_modules():
            action_node = generate_action()
            add_action_arguments(action_node, {})
            call_action(action_node, test_node_idtf)
            wait_agent(1, action_node, ScKeynodes[ActionStatus.ACTION_FINISHED])
            result = check_connector(
                sc_type.VAR_PERM_POS_ARC,
                ScKeynodes[ActionStatus.ACTION_FINISHED_SUCCESSFULLY],
                action_node,
            )
            self.assertTrue(result)
        self.server.remove_modules(module)

    def test_call_action_with_arguments(self):
        module = ScModuleTest()
        self.server.add_modules(module)
        with self.server.register_modules():
            action_node = generate_action()
            node1 = generate_node(sc_type.CONST_NODE)
            node2 = generate_node(sc_type.CONST_NODE)
            add_action_arguments(action_node, {node1: False, node2: False})
            call_action(action_node, test_node_idtf)
            wait_agent(1, action_node, ScKeynodes[ActionStatus.ACTION_FINISHED])
            self.assertEqual(search_element_by_role_relation(action_node, ScKeynodes.rrel_index(1)), node1)
            self.assertEqual(search_element_by_role_relation(action_node, ScKeynodes.rrel_index(2)), node2)
            result = check_connector(
                sc_type.VAR_PERM_POS_ARC,
                ScKeynodes[ActionStatus.ACTION_FINISHED_SUCCESSFULLY],
                action_node,
            )
            self.assertTrue(result)
        self.server.remove_modules(module)

    def test_call_action_with_arguments_in_wrong_order(self):
        module = ScModuleTest()
        self.server.add_modules(module)
        with self.server.register_modules():
            action_node = generate_action()
            node1 = generate_node(sc_type.CONST_NODE)
            node2 = generate_node(sc_type.CONST_NODE)
            add_action_arguments(action_node, {node2: False, node1: False})
            call_action(action_node, test_node_idtf)
            wait_agent(1, action_node, ScKeynodes[ActionStatus.ACTION_FINISHED])
            self.assertEqual(search_element_by_role_relation(action_node, ScKeynodes.rrel_index(1)), node2)
            self.assertEqual(search_element_by_role_relation(action_node, ScKeynodes.rrel_index(2)), node1)
            result = check_connector(
                sc_type.VAR_PERM_POS_ARC,
                ScKeynodes[ActionStatus.ACTION_FINISHED_SUCCESSFULLY],
                action_node,
            )
            self.assertTrue(result)
        self.server.remove_modules(module)

    def test_wrong_execute_action(self):
        module = ScModuleTest()
        self.server.add_modules(module)
        with self.server.register_modules():
            action_node = generate_action()
            add_action_arguments(action_node, {})
            self.assertFalse(execute_action(action_node, "wrong_agent", wait_time=1))
        self.server.remove_modules(module)

    def test_wait_action(self):
        module = ScModuleTest()
        self.server.add_modules(module)
        with self.server.register_modules():
            action_node = generate_action()
            timeout = 0.5
            # Action is not finished while waiting
            start_time = time.time()
            wait_agent(timeout, action_node, ScKeynodes[ActionStatus.ACTION_FINISHED])
            timedelta = time.time() - start_time
            self.assertGreater(timedelta, timeout)
            # Action is finished while waiting
            call_action(action_node, test_node_idtf)
            start_time = time.time()
            wait_agent(timeout, action_node, ScKeynodes[ActionStatus.ACTION_FINISHED])
            timedelta = time.time() - start_time
            self.assertLess(timedelta, timeout)
            # Action finished before waiting
            call_action(action_node, test_node_idtf)
            time.sleep(0.1)
            start_time = time.time()
            wait_agent(timeout, action_node, ScKeynodes[ActionStatus.ACTION_FINISHED])
            timedelta = time.time() - start_time
            self.assertLess(timedelta, timeout)
        self.server.remove_modules(module)
