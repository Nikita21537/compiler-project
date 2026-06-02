from .constant_folding import ConstantFoldingPass
from .constant_propagation import ConstantPropagationPass
from .dead_code_elimination import DeadCodeEliminationPass
from .dead_store_elimination import DeadStoreEliminationPass

__all__ = [
    'ConstantFoldingPass',
    'ConstantPropagationPass',
    'DeadCodeEliminationPass',
    'DeadStoreEliminationPass',
]