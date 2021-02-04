import uuid
import os
from workflows_engine import Workflow, validators
from workflows_engine.core import components as core_components
from workflows_engine.components import buttons
from dataclasses import dataclass
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
cors = CORS(app, resources={r"/todo/*": {"origins": "*"}})


@dataclass
class InventoryItem:
    id: str
    label: str
    checked: bool


TODO_ITEMS = set()


class ToDo(Workflow):
    def _add_item_subflow(self):
        # add_task returns the created task
        # this allows you to access subflows and add tasks to them
        add_item_flow = self.add_task(
            task_type="flow",
            # All tasks require a name this is because it is possible to
            # jump to a task (within the same flow or an ancestor) by its name note this
            # does mean that names should be unique
            name="AddItemSubflow",
            # Preconditions defined if a task should be run if the validator returns True then
            # the precondition passes and the task is ran otherwise the flow moves on to the
            # next task
            preconditions=validators.is_true(identifier="add_item", value_key="$.add_item"),
        )

        # Note: as this task is a child of `AddItemSubflow`
        # it will only be ran if the parent passes its precontion check
        add_item_flow.add_task(
            # screen tasks display there components to the user
            task_type="screen",
            name="AddItemScreen",
            # components can be initialise on the fly or created ahead of time then passed to the task
            components=[
                core_components.Input(identifier="input_item_label", destination_path="item_label"),
                buttons.submit(text="Save"),
                buttons.back(),
            ],
        )

        # jsonrpc tasks make http requests with json as the application type
        add_item_flow.add_task(
            task_type="jsonrpc",
            name="AddItem",
            url="/todo/add_item",
            method="POST",
            # the request payload is constructed from the payload paths
            # which have a src (key) -> destination (result_key) patten
            # to allow for renaming variable and restructuring of the data.
            payload_paths=[{"key": "$.item_label", "result_key": "$.label"}],
            payload={"label": None},
            # There is an optional response path which allows storage of returned values in this
            # case it is not required.
        )

    def _sync_items_subflow(self):
        sync_items_flow = self.add_task(
            task_type="flow",
            name="Add item subflow",
            preconditions=validators.is_false(identifier="not_add_item", value_key="$.add_item"),
        )

        sync_items_flow.add_task(
            task_type="jsonrpc",
            name="SyncItems",
            url="/todo/mark_as_done",
            method="POST",
            payload_paths=[{"key": "$.checked_items", "result_key": "$.checked_items"}],
            payload={"checked_items": []},
        )

        sync_items_flow.add_task(
            task_type="jsonrpc",
            name="ClearCheckedItems",
            preconditions=validators.is_true(
                identifier="should_clear_checked_items", value_key="$.clear_checked"
            ),
            url="/todo/clear_checked",
            method="POST",
        )

    def flow(self, flow_url="/"):
        # Add a screen task to display the todo list.
        self.add_task(
            task_type="screen",
            name="ToDoScreen",
            components=[
                # The check box creates a check box for each of the items in `context["items"]`
                # the checkbox is considered checked if its `value` is in the context under the target
                # in this case `context["checked_items"]`.
                core_components.Checkbox(title="Items", data="$.items", target="$.checked_items"),
                [
                    # Note: here a list as item in the component list means
                    # that the components will be put on the same row
                    buttons.submit(text="Save"),
                    buttons.next(
                        text="Add Item",
                        style="secondary",
                        value=True,
                        destination_path="$.add_item",  # This will be used for flow control later
                    ),
                ],
                buttons.next(
                    text="Clear completed items",
                    style="secondary",
                    value=True,
                    destination_path="$.clear_checked",  # This will be used for flow control later
                ),
            ],
        )

        # Note: sub flow tasks created in _add_item_subflow and _sync_items_subflow
        # have preconditions which are opposites this allows the variable
        # add_item to control the path of the flow.

        # Add screen and endpoints to add item to list
        self._add_item_subflow()

        # Add endpoint calls to sync checked items and clear checked items
        self._sync_items_subflow()

        # Redirect to the flow url so that we reload the the flow with the new items
        self.add_task(task_type="redirect", name="reload", url=flow_url)
        # this could also be done as a while loop and an endpoint to fetch the infomation instead
        # but this is a simple approach which also allows for the flow to change.
        # There is plans to cache flows then to only send the "context" key, which would
        # make this reload method more efficient.


########################## helpers #############################################


def get_checked_items():
    return {item for item in TODO_ITEMS if item.checked}


############ Endpoints to serve the client ####################################


@app.route("/", methods=["GET"])
def show_list():
    return jsonify(
        ToDo(
            context={
                "clear_checked": False,
                "add_item": False,
                "checked_items": [i.id for i in get_checked_items()],
                "items": [{"label": item.label, "value": item.id} for item in TODO_ITEMS],
            }
        ).as_dict()
    )


@app.route("/add_item", methods=["POST"])
def add_item():
    payload = request.json
    label = payload.get("item", False)
    if not label:
        return jsonify({"error": {"data": {"message": "Missing item text"}}})

    TODO_ITEMS.add(Item(id=uuid.uuid4().hex, label=label, checked=False))
    return jsonify(True)


@app.route("/mark_as_done", methods=["POST"])
def mark_as_done():
    payload = request.json
    items_ids_to_mark = payload.get("checked_items", False)
    if not items_ids_to_mark:
        return jsonify({"error": {"data": {"message": "No checked items provided"}}})

    unchecked_items = TODO_ITEMS - get_checked_items()
    for list_item in unchecked_items:
        if list_item.id in items_ids_to_mark:
            list_item.checked = True


@app.route("/clear_checked_items", methods=["POST"])
def clear_checked():
    for item in get_checked_items():
        TODO_ITEMS.remove(item)
        del item


if __name__ == "__main__":
    app.run()
