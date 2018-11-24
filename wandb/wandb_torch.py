#!/usr/bin/env python

"""PyTorch-specific functionality
"""

from collections import namedtuple
import weakref
from six.moves import reduce
from distutils.version import LooseVersion
from operator import mul


from wandb import util
from wandb.data_types import Node, Edge, Graph
import wandb

torch = None


def nested_shape(array_or_tuple):
    """Figures out the shape of tensors possibly embedded in tuples
     i.e 
     [0,0] returns (2)
     ([0,0], [0,0]) returns (2,2)
     (([0,0], [0,0]),[0,0]) returns ((2,2),2)
     """
    if hasattr(array_or_tuple, 'size'):
        # pytorch tensors use V.size() to get size of tensor
        return list(array_or_tuple.size())
    elif hasattr(array_or_tuple, 'get_shape'):
        # tensorflow uses V.get_shape() to get size of tensor
        return array_or_tuple.get_shape().as_list()
    elif hasattr(array_or_tuple, 'shape'):
        return array_or_tuple.shape

    try:
        #treat object as iterable
        return [nested_shape(item) for item in list(array_or_tuple)]
    except TypeError:
        # object is not actually iterable
        # LB: Maybe we should throw an error?
        return []

def has_submodules( module):
    global torch
    if torch is None:
        torch = wandb.util.get_module("torch", "Could not import torch")
    # Trying to support torch >0.3 making this code complicated
    # We want a list of types that we should recurse into
    # Torch 0.3   uses containers
    #       0.4   has ModuleList
    #       0.4.1 has ModuleDict
    module_types = [getattr(torch.nn, module_classname)
        for module_classname in ("Container", "Sequential", "ModuleList", "ModuleDict")
        if hasattr(torch.nn, module_classname)]
        
    return isinstance(module, tuple(module_types))

class TorchHistory(object):
    """History methods specific to PyTorch
    """

    def __init__(self, history):
        global torch
        torch = wandb.util.get_module("torch", "Could not import torch")
        self._history = weakref.ref(history)
        self._hook_handles = {}

    def add_log_hooks_to_pytorch_module(self, module, name=None, prefix='', log_parameters=True, log_gradients=True):
        """ This instuments hooks into the pytorch module
        log_parameters - log parameters after a forward pass
        log_gradients - log gradients after a backward pass
        """
        if prefix != '':
            prefix += "/"

        if name is not None:
            prefix = prefix + name

        def parameter_log_hook(module, input_, output):
            for name, parameter in module.named_parameters():
                # for pytorch 0.3 Variables
                if isinstance(parameter, torch.autograd.Variable):
                    data = parameter.data
                else:
                    data = parameter
                self.log_tensor_stats(data, 'parameters/' + prefix + name)

        if log_parameters:
            module.register_forward_hook(parameter_log_hook)

        # This won't handle the case if the network changes
        if log_gradients:
            for name, parameter in module.named_parameters():
                self._hook_variable_gradient_stats(
                    parameter, 'gradients/' + prefix + name)

    def log_tensor_stats(self, tensor, name):
        """Add distribution statistics on a tensor's elements to the current History entry
        """

        # LB We could potentially speed this up by using pytorch's torch.histc instead of
        # converting to numpy
        # TODO Handle the case of duplicate names.

        if (isinstance(tensor, tuple) or isinstance(tensor, list)):
            while (isinstance(tensor, tuple) or isinstance(tensor, list)) and (isinstance(tensor[0], tuple) or isinstance(tensor[0], list)):
                tensor = [item for sublist in tensor for item in sublist]
            tensor = torch.cat([t.view(-1) for t in tensor])

        # checking for inheritance from _TensorBase didn't work for some reason
        if not hasattr(tensor, 'shape'):
            cls = type(tensor)
            raise TypeError('Expected Tensor, not {}.{}'.format(
                cls.__module__, cls.__name__))
        history = self._history()
        if history is None or not history.compute:
            return
        flat = tensor.view(-1)

        # detach is new in 0.4
        tensor = flat.cpu().clone()
        if (hasattr(tensor, "detach")):
            tensor = tensor.detach()
        else:
            tensor = tensor.numpy()

        history.row.update({
            name: wandb.Histogram(tensor)
        })

    def _hook_variable_gradient_stats(self, var, name):
        """Logs a Variable's gradient's distribution statistics next time backward()
        is called on it.
        """
        if not isinstance(var, torch.autograd.Variable):
            cls = type(var)
            raise TypeError('Expected torch.Variable, not {}.{}'.format(
                cls.__module__, cls.__name__))

        handle = self._hook_handles.get(name)
        if handle is not None and self._torch_hook_handle_is_valid(handle):
            raise ValueError(
                'A hook has already been set under name "{}"'.format(name))

        def _callback(grad):
            self.log_tensor_stats(grad.data, name)

        handle = var.register_hook(_callback)
        self._hook_handles[name] = handle
        return handle

    def unhook(self, name):
        handle = self._hook_handles.pop(name)
        handle.remove()


    def _torch_hook_handle_is_valid(handle):
        d = handle.hooks_dict_ref()
        if d is None:
            return False
        else:
            return handle.id in d

class TorchGraph():
       
    def __init__(self):
        self.module_graph = Graph('torch')
        self.forward_graph = Graph('torch')
        self.backward_graph = Graph('torch')

    @classmethod
    def hook_torch(cls, model, criterion=None):
        graph = TorchGraph()
        graph.hook_torch_modules(model, criterion)
        graph.model = model
        return graph

    def save_forward_graph_from_jit_trace(self, input_data):
        # modifid from https://github.com/szagoruyko/pytorchviz/blob/master/torchviz/dot.py
        # won't work with pytorch <1.0

        trace, _ = torch.jit.get_trace_graph(self.model, args=(input_data,))
        if LooseVersion(torch.__version__) >= LooseVersion("0.4.1"):
            torch.onnx._optimize_trace(trace, torch._C._onnx.OperatorExportTypes.ONNX_ATEN_FALLBACK)
        elif LooseVersion(torch.__version__) >= LooseVersion("0.4"):
            torch.onnx._optimize_trace(trace, False)
        else:
            torch.onnx._optimize_trace(trace)
        graph = trace.graph()
        list_of_nodes = parse(graph)
        
        for node in list_of_nodes:
            self.forward_graph.add_node(node.name)
            if node.inputs:
                for inp in node.inputs:
                    self.forward_graph.add_edge(inp.name, node.name)

    def log_graph_on_next_backwards_pass(self):
        print(self.model)
        def after_backward_hook(module, input, output):
            self.save_backward_graph(output)
            handle.remove()

        handle = self.model.register_backward_hook(after_backward_hook)
        
    def save_backward_graph(self, var):
        print("Saving graph", var)
        seen = set()

        def size_to_str(size):
            return '(' + (', ').join(['%d' % v for v in size]) + ')'

        output_nodes = (var.grad_fn,) if not isinstance(var, tuple) else tuple(v.grad_fn for v in var)

        def add_nodes(var):
            if var not in seen:
                print("Here")
                if torch.is_tensor(var):
                    # note: this used to show .saved_tensors in pytorch0.2, but stopped
                    # working as it was moved to ATen and Variable-Tensor merged
                    self.backward_graph.add_node(str(id(var)))
                elif hasattr(var, 'variable'):
                    u = var.variable
                    node_name = '%s' % size_to_str(u.size())
                    self.backward_graph.add_node(id=str(id(var)), name=node_name)

                elif var in output_nodes:
                    self.backward_graph.add_node(id=str(id(var)), name=str(type(var).__name__))
                else:
                    self.backward_graph.add_node(id=str(id(var)), name=str(type(var).__name__))

                seen.add(var)
                if hasattr(var, 'next_functions'):
                    for u in var.next_functions:
                        if u[0] is not None:
                            add_nodes(u[0])
                            self.backward_graph.add_edge(str(id(u[0])), str(id(var)))
                if hasattr(var, 'saved_tensors'):
                    for t in var.saved_tensors:
                        add_nodes(t)
                        self.backward_graph.add_edge(str(id(t)), str(id(var)))

        # handle multiple outputs
        if isinstance(var, tuple):
            for v in var:
                add_nodes(v.grad_fn)
        else:
            add_nodes(var.grad_fn)

    def create_forward_hook(self, name, modules):
        """Adds module nodes to the graph"""

        graph = self.module_graph

        def after_forward_hook(module, input, output):
            if id(module) in modules:
                return
            modules.add(id(module))
            if not isinstance(output, tuple):
                output = (output,)
            parameters = [(pname, list(param.size()))
                          for pname, param in module.named_parameters()]

            node = Node(
                id=id(module),
                name=name,
                class_name=str(module),
                output_shape=nested_shape(output),
                parameters=parameters,
                num_parameters=[reduce(mul, size)
                                for (pname, size) in parameters]
            )
            graph.nodes_by_id[id(module)] = node
            for param in module.parameters():
                graph.nodes_by_id[id(param)] = node
            graph.add_node(node)
            if not graph.criterion_passed:
                graph.criterion = output[0].grad_fn
        return after_forward_hook

    def hook_torch_modules(self, module, criterion=None, prefix=None):
        """Builds up a graph of the modules torch is using and add a forward hook
        that saves as nodes all of the modules called.
        """

        torch = util.get_module("torch", "Could not import torch")
        hooks = []
        modules = set()
        layers = 0
        graph = self
        if criterion:
            graph.criterion = criterion
            graph.criterion_passed = True

        for name, sub_module in module.named_children():
            name = name or str(layers)
            if prefix:
                name = prefix + "." + name
            layers += 1
            if not isinstance(sub_module, torch.nn.Module):
                # TODO: Why does this happen?
                break

            if has_submodules(sub_module):
                self.hook_torch_modules(sub_module, prefix=name)
            else:
                hooks.append(
                    sub_module.register_forward_hook(self.create_forward_hook(name, modules)))
