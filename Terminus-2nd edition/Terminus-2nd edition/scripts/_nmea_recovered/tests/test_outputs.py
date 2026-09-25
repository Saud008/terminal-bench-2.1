        finally:
            if dynamic.exists():
                dynamic.unlink()

    def test_session_replay_replaces_duplicate_fragment(self) -> None:
        """Session replay must keep the later