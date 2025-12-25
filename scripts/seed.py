import random
import uuid
from datetime import datetime, timedelta

from sqlalchemy import insert
from sqlalchemy.orm import Session

from app.db.session import engine
from app.models.models import (
    Artifact,
    Dataset,
    DatasetVersion,
    Experiment,
    MetricDefinition,
    MLProject,
    OrgMember,
    Organization,
    ProjectMember,
    Run,
    RunArtifact,
    RunConfig,
    RunMetricValue,
    User,
)


def _random_email(index: int) -> str:
    return f"user{index}@example.com"


def _random_name(index: int) -> str:
    return f"User {index}"


def _random_hash() -> str:
    return uuid.uuid4().hex


def seed() -> None:
    random.seed(42)

    with Session(engine) as db:
        metric_defs = [
            MetricDefinition(
                metric_id=uuid.uuid4(),
                key="accuracy",
                display_name="Accuracy",
                unit="ratio",
                goal="max",
            ),
            MetricDefinition(
                metric_id=uuid.uuid4(),
                key="val_loss",
                display_name="Validation Loss",
                unit="loss",
                goal="min",
            ),
            MetricDefinition(
                metric_id=uuid.uuid4(),
                key="f1",
                display_name="F1",
                unit="ratio",
                goal="max",
            ),
            MetricDefinition(
                metric_id=uuid.uuid4(),
                key="auc",
                display_name="AUC",
                unit="ratio",
                goal="max",
            ),
        ]
        db.add_all(metric_defs)
        db.commit()

        users = [
            User(
                user_id=uuid.uuid4(),
                email=_random_email(i),
                full_name=_random_name(i),
                password_hash=_random_hash(),
                is_active=True,
            )
            for i in range(1, 501)
        ]
        db.add_all(users)
        db.commit()

        orgs: list[Organization] = []
        for i in range(1, 6):
            org = Organization(
                org_id=uuid.uuid4(),
                name=f"Org {i}",
                description=f"Organization {i}",
                created_by=random.choice(users).user_id,
            )
            orgs.append(org)
        db.add_all(orgs)
        db.commit()

        org_members: list[OrgMember] = []
        for org in orgs:
            members = random.sample(users, 20)
            for member in members:
                role = "member"
                if member.user_id == org.created_by:
                    role = "owner"
                org_members.append(
                    OrgMember(
                        org_member_id=uuid.uuid4(),
                        org_id=org.org_id,
                        user_id=member.user_id,
                        role=role,
                        is_active=True,
                    )
                )
        db.add_all(org_members)
        db.commit()

        projects: list[MLProject] = []
        for org in orgs:
            for idx in range(4):
                project = MLProject(
                    project_id=uuid.uuid4(),
                    org_id=org.org_id,
                    name=f"Project {org.name}-{idx + 1}",
                    description="Demo project",
                    status="active",
                )
                projects.append(project)
        db.add_all(projects)
        db.commit()

        project_members: list[ProjectMember] = []
        for project in projects:
            members = random.sample(users, 10)
            for member in members:
                project_members.append(
                    ProjectMember(
                        project_member_id=uuid.uuid4(),
                        project_id=project.project_id,
                        user_id=member.user_id,
                        role=random.choice(["admin", "editor", "viewer"]),
                        is_active=True,
                    )
                )
        db.add_all(project_members)
        db.commit()

        datasets: list[Dataset] = []
        for project in projects:
            for idx in range(3):
                datasets.append(
                    Dataset(
                        dataset_id=uuid.uuid4(),
                        project_id=project.project_id,
                        name=f"Dataset {idx + 1} - {project.name}",
                        task_type=random.choice(
                            [
                                "classification",
                                "regression",
                                "ranking",
                                "segmentation",
                                "nlp",
                                "other",
                            ]
                        ),
                        description="Seed dataset",
                    )
                )
        db.add_all(datasets)
        db.commit()

        dataset_versions: list[DatasetVersion] = []
        for dataset in datasets:
            for idx in range(2):
                dataset_versions.append(
                    DatasetVersion(
                        dataset_version_id=uuid.uuid4(),
                        dataset_id=dataset.dataset_id,
                        version_label=f"v{idx + 1}",
                        storage_uri=f"s3://bucket/{dataset.dataset_id}/v{idx + 1}",
                        content_hash=_random_hash(),
                        row_count=random.randint(1000, 100000),
                        size_bytes=random.randint(1_000_000, 50_000_000),
                        schema_json={"columns": ["f1", "f2", "label"]},
                    )
                )
        db.add_all(dataset_versions)
        db.commit()

        experiments: list[Experiment] = []
        for project in projects:
            for idx in range(5):
                experiments.append(
                    Experiment(
                        experiment_id=uuid.uuid4(),
                        project_id=project.project_id,
                        name=f"Exp {idx + 1} - {project.name}",
                        objective="Optimize metric",
                        created_by=random.choice(users).user_id,
                    )
                )
        db.add_all(experiments)
        db.commit()

        runs: list[Run] = []
        run_configs: list[RunConfig] = []
        for exp in experiments:
            for idx in range(10):
                dataset_version = random.choice(dataset_versions)
                run_id = uuid.uuid4()
                started_at = datetime.utcnow() - timedelta(days=random.randint(0, 30))
                finished_at = started_at + timedelta(minutes=random.randint(5, 240))
                status = random.choice(["finished", "failed", "killed"])
                runs.append(
                    Run(
                        run_id=run_id,
                        experiment_id=exp.experiment_id,
                        dataset_version_id=dataset_version.dataset_version_id,
                        run_name=f"run-{idx + 1}",
                        status=status,
                        started_at=started_at,
                        finished_at=finished_at if status == "finished" else None,
                        created_by=random.choice(users).user_id,
                        git_commit=_random_hash()[:8],
                        notes="seed",
                    )
                )
                run_configs.append(
                    RunConfig(
                        run_id=run_id,
                        params_json={"lr": random.choice([0.1, 0.01, 0.001])},
                        env_json={"python": "3.12", "cuda": "12.1"},
                        command_line="python train.py",
                        seed=random.randint(1, 10000),
                    )
                )
        db.add_all(runs)
        db.add_all(run_configs)
        db.commit()

        artifacts: list[Artifact] = []
        for project in projects:
            for idx in range(10):
                artifacts.append(
                    Artifact(
                        artifact_id=uuid.uuid4(),
                        project_id=project.project_id,
                        artifact_type=random.choice(
                            ["model", "plot", "log", "report", "dataset-sample", "other"]
                        ),
                        uri=f"s3://artifacts/{project.project_id}/{idx}",
                        checksum=_random_hash(),
                        size_bytes=random.randint(1000, 10_000_000),
                    )
                )
        db.add_all(artifacts)
        db.commit()

        run_artifacts: list[RunArtifact] = []
        for run in runs:
            artifact = random.choice(artifacts)
            run_artifacts.append(
                RunArtifact(
                    run_artifact_id=uuid.uuid4(),
                    run_id=run.run_id,
                    artifact_id=artifact.artifact_id,
                    alias=random.choice(["best_model", "confusion_matrix", "log"]),
                )
            )
        db.add_all(run_artifacts)
        db.commit()

        metric_map = {m.key: m.metric_id for m in metric_defs}
        final_metrics = []
        step_metrics = []
        for run in runs:
            for key in metric_map:
                final_metrics.append(
                    {
                        "run_metric_value_id": uuid.uuid4(),
                        "run_id": run.run_id,
                        "metric_id": metric_map[key],
                        "scope": "val",
                        "step": None,
                        "value": random.uniform(0.1, 0.99),
                    }
                )

            for step in range(20):
                step_metrics.append(
                    {
                        "run_metric_value_id": uuid.uuid4(),
                        "run_id": run.run_id,
                        "metric_id": metric_map["accuracy"],
                        "scope": "train",
                        "step": step,
                        "value": random.uniform(0.1, 0.99),
                    }
                )
                step_metrics.append(
                    {
                        "run_metric_value_id": uuid.uuid4(),
                        "run_id": run.run_id,
                        "metric_id": metric_map["val_loss"],
                        "scope": "val",
                        "step": step,
                        "value": random.uniform(0.1, 2.5),
                    }
                )

        db.execute(insert(RunMetricValue), final_metrics)
        db.execute(insert(RunMetricValue), step_metrics)
        db.commit()

        print(
            f"Seed complete: users={len(users)}, projects={len(projects)}, runs={len(runs)}, "
            f"run_metric_values={len(final_metrics) + len(step_metrics)}"
        )


if __name__ == "__main__":
    seed()
