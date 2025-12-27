from typing import Literal

ProjectStatus = Literal["active", "archived"]
RunStatus = Literal["queued", "running", "finished", "failed", "killed"]

OrgMemberRole = Literal["owner", "admin", "member", "viewer"]
ProjectMemberRole = Literal["admin", "editor", "viewer"]

TaskType = Literal["classification", "regression", "ranking", "segmentation", "nlp", "other"]
MetricGoal = Literal["min", "max", "last"]
MetricScope = Literal["train", "val", "test"]

ArtifactType = Literal["model", "plot", "log", "report", "dataset-sample", "other"]

BatchJobType = Literal["users", "datasets", "runs", "metrics", "artifacts"]
BatchJobStatus = Literal["created", "running", "finished", "failed"]
SourceFormat = Literal["csv", "json"]
