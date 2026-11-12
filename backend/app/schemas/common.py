"""共享 Pydantic 基类：统一 camelCase 序列化。"""
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """所有响应模型继承此基类，输出与前端 `src/types` 1:1 对齐的 camelCase JSON。

    `populate_by_name=True` 允许以字段名（snake_case）构造，别名仅用于序列化输出。
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
