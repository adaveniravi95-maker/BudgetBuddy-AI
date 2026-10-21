"""${message}"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
${imports or ""}
revision: str = ${repr(up_revision)}
down_revision: Union[str, Sequence[str], None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}

def upgrade() -> None:
    ${upgrades or "pass"}

def downgrade() -> None:
    ${downgrades or "pass"}
