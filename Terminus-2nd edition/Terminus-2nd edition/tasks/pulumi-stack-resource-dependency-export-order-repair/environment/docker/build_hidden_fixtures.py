#!/usr/bin/env python3
"""Image-build helper: hidden stack snapshots at /opt/verifier-fixtures (not under /app)."""

from __future__ import annotations

import json
from pathlib import Path

OUT_ROOT = Path("/opt/verifier-fixtures/pulumi-dep")
OUT_STACKS = OUT_ROOT / "stacks"

HIDDEN_NESTED_DBR = {
    "stack": "hidden-nested",
    "version": 3,
    "deployment": {
        "resources": [
            {
                "urn": "urn:pulumi:hidden::acme::pulumi:providers:aws::default",
                "type": "pulumi:providers:aws",
                "parent": "urn:pulumi:hidden::acme::pulumi:stack$acme/hidden",
            },
            {
                "urn": "urn:pulumi:hidden::acme::custom:module:Net::core",
                "type": "custom:module:Net",
                "parent": "urn:pulumi:hidden::acme::pulumi:stack$acme/hidden",
                "component": True,
            },
            {
                "urn": "urn:pulumi:hidden::acme::aws:ec2/vpc:Vpc::core/vpc",
                "type": "aws:ec2/vpc:Vpc",
                "parent": "urn:pulumi:hidden::acme::custom:module:Net::core",
                "provider": "urn:pulumi:hidden::acme::pulumi:providers:aws::default",
            },
            {
                "urn": "urn:pulumi:hidden::acme::aws:iam/role:Role::core/role",
                "type": "aws:iam/role:Role",
                "parent": "urn:pulumi:hidden::acme::custom:module:Net::core",
                "provider": "urn:pulumi:hidden::acme::pulumi:providers:aws::default",
                "dependencies": [
                    "urn:pulumi:hidden::acme::aws:ec2/vpc:Vpc::core/vpc"
                ],
            },
            {
                "urn": "urn:pulumi:hidden::acme::aws:s3/bucket:Bucket::data-old",
                "type": "aws:s3/bucket:Bucket",
                "parent": "urn:pulumi:hidden::acme::pulumi:stack$acme/hidden",
                "provider": "urn:pulumi:hidden::acme::pulumi:providers:aws::default",
            },
            {
                "urn": "urn:pulumi:hidden::acme::aws:s3/bucket:Bucket::data-new",
                "type": "aws:s3/bucket:Bucket",
                "parent": "urn:pulumi:hidden::acme::pulumi:stack$acme/hidden",
                "provider": "urn:pulumi:hidden::acme::pulumi:providers:aws::default",
                "deleteBeforeReplace": True,
                "replaces": "urn:pulumi:hidden::acme::aws:s3/bucket:Bucket::data-old",
            },
            {
                "urn": "urn:pulumi:hidden::acme::aws:s3/bucketObject:BucketObject::data-new/lock",
                "type": "aws:s3/bucketObject:BucketObject",
                "parent": "urn:pulumi:hidden::acme::pulumi:stack$acme/hidden",
                "provider": "urn:pulumi:hidden::acme::pulumi:providers:aws::default",
                "dependencies": [
                    "urn:pulumi:hidden::acme::aws:s3/bucket:Bucket::data-new",
                    "urn:pulumi:hidden::acme::aws:iam/role:Role::core/role",
                ],
            },
        ]
    },
}

HIDDEN_EPOCH = {
    "stack": "hidden-epoch",
    "version": 3,
    "deployment": {
        "resources": [
            {
                "urn": "urn:pulumi:epoch::acme::pulumi:providers:aws::default",
                "type": "pulumi:providers:aws",
                "parent": "urn:pulumi:epoch::acme::pulumi:stack$acme/epoch",
            },
            {
                "urn": "urn:pulumi:epoch::acme::aws:s3/bucket:Bucket::only",
                "type": "aws:s3/bucket:Bucket",
                "parent": "urn:pulumi:epoch::acme::pulumi:stack$acme/epoch",
                "provider": "urn:pulumi:epoch::acme::pulumi:providers:aws::default",
            },
        ]
    },
}


def build() -> None:
    OUT_STACKS.mkdir(parents=True, exist_ok=True)
    (OUT_STACKS / "hidden-nested-dbr.json").write_text(
        json.dumps(HIDDEN_NESTED_DBR, indent=2) + "\n",
        encoding="utf-8",
    )
    (OUT_STACKS / "hidden-epoch-carry.json").write_text(
        json.dumps(HIDDEN_EPOCH, indent=2) + "\n",
        encoding="utf-8",
    )
    catalog = {
        "scenarios": [
            {
                "name": "hidden-nested-dbr",
                "stack": "stacks/hidden-nested-dbr.json",
            },
            {
                "name": "hidden-epoch-carry",
                "stack": "stacks/hidden-epoch-carry.json",
            },
        ]
    }
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    (OUT_ROOT / "catalog.json").write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    build()
