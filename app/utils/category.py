from typing import Deque
from collections import deque

from catalog.models.category import Category


def calculate_maximal_children_depth(
    category: Category,
) -> int:
    """Calculate what is the maximal depth that can branched from a category using BFS, and
    taking advantage of stored ``depth`` within each ``Category``.

    Example tree::
      A -> B -> C
           B -> D -> E

    In the example above, `calculate_children_depth` of `A` will be 4.
    """

    remained_categories: Deque[Category] = deque()
    maximal_depth = 0

    remained_categories.append(category)
    while len(remained_categories) > 0:
        current_category = remained_categories.popleft()
        maximal_depth = max(
            maximal_depth,
            current_category.depth - category.depth,
            # `current_category.depth` alone will not work
            # subtraction is needed to correct the result
        )

        if current_category.children:
            remained_categories.extend(current_category.children)

    return maximal_depth
