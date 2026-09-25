IKE unique-id lifecycle

ike_up allocates an IKE_SA unique-id slot. The slot remains reserved until ike_down for that same unique-id. child_delete_response must not release IKE_SA slots. child_up does not allocate IKE slots. Reusing an in-use IKE unique-id before ike_down sets uid_ok false, reject_reason uid_reused.
