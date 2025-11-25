from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, model_validator

ALLOWED_CHANNELS = {"email", "slack", "inapp"}


class Template(BaseModel):
    template_id: Optional[int] = None
    template_str: Optional[str] = None
    data: dict = {}

    @model_validator(mode="after")
    def validate_either_or(self):
        if (self.template_id is None) and (self.template_str is None):
            raise ValueError("Either template_id or template_str must be provided")

        if (self.template_id is not None) and (self.template_str is not None):
            raise ValueError("Provide only one: template_id OR template_str")
        return self


class NotificationRequest(BaseModel):
    # either ther should be user group or user id in the request
    user_id: Optional[int] = None
    user_group: Optional[int] = None
    subject: Optional[str] = 'Notification'
    message: str
    template: Optional[Template] = None
    channels: List[str]
    scheduled_time: Optional[str] = None

    @model_validator(mode="after")
    def validate_either_or(self):
        if (self.user_id is None) and (self.user_group is None):
            raise ValueError("Either user_id or user_group must be provided")

        if (self.user_id is not None) and (self.user_group is not None):
            raise ValueError("Provide only one: user_id OR user_group")

        if self.scheduled_time is not None:
            try:
                datetime.strptime(self.scheduled_time, "%Y-%m-%dT%H:%M:%S")
            except ValueError:
                raise ValueError("scheduled_time must be in format YYYY-MM-DDTHH:MM:SS")

        v = self.channels

        # 1. At least one
        if not v:
            raise ValueError("At least one channel must be provided.")

        # 2. At most three
        if len(v) > 3:
            raise ValueError("At most three channels are allowed.")

        # 3. No duplicates
        if len(v) != len(set(v)):
            raise ValueError("Duplicate channels are not allowed.")

        # 4. Only allowed values
        invalid = set(v) - ALLOWED_CHANNELS
        if invalid:
            raise ValueError(
                f"Invalid channels: {invalid}. Allowed: {ALLOWED_CHANNELS}"
            )
        return self


def render_template(t:str , data) -> str:
    if not t:
        raise ValueError("template_str is required when using a template")

    try:
        print(  t , data)
        return t.format(**data)
    except KeyError as e:
        raise ValueError(f"Missing template data key: {e}")