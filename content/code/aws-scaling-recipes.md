---
title: "AWS Scaling Recipes: EC2 and ASG in Shell Scripts"
date: 2026-02-15
comments: true
---

**AWS Scaling Recipes**: Practical shell scripts for EC2 vertical scaling and Auto Scaling Group horizontal scaling — runbook patterns you can actually commit to a repository and trust in production.

## The Problem With Cloud Tutorials

Most AWS documentation teaches you to click through the console. That works once. The second time you need it, you click through again. The third time, you're clicking through at 2 AM wondering if you're remembering the right sequence.

The alternative is scripts. Not the kind that wrap every AWS CLI call in five layers of abstraction, but the kind you can read top to bottom in three minutes and understand completely.

AWS Scaling Recipes is that kind of scripts.

## Vertical Scaling: Growing a Single Instance

Vertical scaling means making one machine bigger. You stop the instance, change the instance type, start it again. Straightforward in principle, error-prone in practice because the order matters and the AWS CLI doesn't hold your hand.

```bash
#!/usr/bin/env bash
set -euo pipefail

INSTANCE_ID="$1"
NEW_TYPE="$2"

echo "Stopping $INSTANCE_ID..."
aws ec2 stop-instances --instance-ids "$INSTANCE_ID"
aws ec2 wait instance-stopped --instance-ids "$INSTANCE_ID"

echo "Changing instance type to $NEW_TYPE..."
aws ec2 modify-instance-attribute \
  --instance-id "$INSTANCE_ID" \
  --instance-type "{\"Value\": \"$NEW_TYPE\"}"

echo "Starting $INSTANCE_ID..."
aws ec2 start-instances --instance-ids "$INSTANCE_ID"
aws ec2 wait instance-running --instance-ids "$INSTANCE_ID"

echo "Done. New type: $NEW_TYPE"
```

The `set -euo pipefail` at the top is non-negotiable for any script that touches production infrastructure. Exit on error. Exit on unset variable. Fail if any command in a pipe fails.

The `aws ec2 wait` calls are equally important — they block until the state transition is complete, so you're not running `modify-instance-attribute` on an instance that's still shutting down.

## Horizontal Scaling: Growing a Fleet

Horizontal scaling means adding more machines of the same type. AWS Auto Scaling Groups handle the lifecycle; the scripts handle the policy management — setting desired capacity, adjusting min/max, attaching and detaching instances.

```bash
# Scale out: increase desired capacity
scale_out() {
  local asg_name="$1"
  local increment="${2:-1}"

  current=$(aws autoscaling describe-auto-scaling-groups \
    --auto-scaling-group-names "$asg_name" \
    --query 'AutoScalingGroups[0].DesiredCapacity' \
    --output text)

  new_desired=$((current + increment))

  aws autoscaling set-desired-capacity \
    --auto-scaling-group-name "$asg_name" \
    --desired-capacity "$new_desired" \
    --honor-cooldown

  echo "Scaled $asg_name from $current to $new_desired"
}

# Scale in: decrease desired capacity
scale_in() {
  local asg_name="$1"
  local decrement="${2:-1}"

  current=$(aws autoscaling describe-auto-scaling-groups \
    --auto-scaling-group-names "$asg_name" \
    --query 'AutoScalingGroups[0].DesiredCapacity' \
    --output text)

  new_desired=$((current - decrement))
  min=$(aws autoscaling describe-auto-scaling-groups \
    --auto-scaling-group-names "$asg_name" \
    --query 'AutoScalingGroups[0].MinSize' \
    --output text)

  if [ "$new_desired" -lt "$min" ]; then
    echo "Cannot scale below minimum ($min)"
    exit 1
  fi

  aws autoscaling set-desired-capacity \
    --auto-scaling-group-name "$asg_name" \
    --desired-capacity "$new_desired" \
    --honor-cooldown
}
```

`--honor-cooldown` respects the ASG's configured cooldown period — the window after a scaling event during which the group won't scale again. Bypassing it is tempting when you're in a hurry and actively harmful when the system is oscillating.

## Waiting for Health

After a scale-out, you want to know that the new instances are actually healthy before declaring success. The ASG knows this; you just need to ask:

```bash
wait_for_healthy() {
  local asg_name="$1"
  local expected_count="$2"

  echo -n "Waiting for $expected_count healthy instances..."
  while true; do
    healthy=$(aws autoscaling describe-auto-scaling-groups \
      --auto-scaling-group-names "$asg_name" \
      --query 'AutoScalingGroups[0].Instances[?HealthStatus==`Healthy`] | length(@)' \
      --output text)

    if [ "$healthy" -ge "$expected_count" ]; then
      echo " done ($healthy healthy)"
      break
    fi
    echo -n "."
    sleep 10
  done
}
```

## The Case for Shell

These are shell scripts rather than Terraform, CDK, or a Python SDK wrapper for a reason. Terraform manages desired state; these scripts manage transitions. When you need to respond to an incident — right now, without running a full plan — shell is what you reach for.

They're also readable by anyone. No knowledge of a framework required. `aws ec2 stop-instances` does exactly what it says.

Store them in your repository. Review them like code. They're runbooks that execute themselves.

## Links

- **GitHub**: [lucianofedericopereira/aws-scaling-recipes](https://github.com/lucianofedericopereira/aws-scaling-recipes)

## License

MIT
