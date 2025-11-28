from pydantic import BaseModel, Field
from typing import Optional, Dict, List



class SSHConfig(BaseModel):
    hostname: str = Field(..., description="Remote server IP or domain")
    username: str = Field(..., description="SSH username")
    password: Optional[str] = Field(
        None, description="SSH password (optional)"
    )
    key_filename: Optional[str] = Field(
        None, description="Path to the private key file"
    )
    port: int = Field(22, description="SSH port")


class PipelineConfig(BaseModel):
    script: str
    args: Optional[List[str]] = Field(
        default_factory=list, description="List of arguments for the script"
    )

class InstanceConfig(BaseModel):
    mode: str
    workdir: str
    target_workdir: str
    requirements: str
    pipelines: Dict[str, PipelineConfig]  # ensures pipelines is a dict, not a list

class ConfigSchema(BaseModel):
    mlflow_uri: str
    experiment_name: str
    instances: List[InstanceConfig]