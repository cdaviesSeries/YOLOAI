In the new `execute_pipeline_from_state` function, there is a potential bug related to the handling of the `pipeline_invocation` object retrieved from the database. Specifically, if the `get_invocation` function returns `None` because the `pipeline_invocation_id` does not correspond to any existing record, the subsequent code will raise an `AttributeError` when trying to access attributes of `None`.

**Issue:**
```python
pipeline_invocation = await get_invocation(pipeline_invocation_id, db)

# check if user_id matches
if user_id != pipeline_invocation.userId:
    raise ValueError("Unauthorized: you are not allowed to access this pipeline invocation")
```

If `pipeline_invocation` is `None`, attempting to access `pipeline_invocation.userId` will result in an `AttributeError`.

**Suggested Fix:**

Add a check to handle the case where `pipeline_invocation` is `None`:

```python
pipeline_invocation = await get_invocation(pipeline_invocation_id, db)

if pipeline_invocation is None:
    raise ValueError(f"No pipeline invocation found with id '{pipeline_invocation_id}'.")

# check if user_id matches
if user_id != pipeline_invocation.userId:
    raise ValueError("Unauthorized: you are not allowed to access this pipeline invocation")
```

This ensures that you explicitly handle the case where the invocation does not exist, providing a clear error message to the user.