class TalentScopeError(Exception):
    pass


class MissingInputError(TalentScopeError):
    pass


class EmptyFileError(TalentScopeError):
    pass


class UnreadableFileError(TalentScopeError):
    """File could not be parsed — route to HITL."""
    pass


class NonEnglishResumeError(TalentScopeError):
    pass


class InvalidResumeError(TalentScopeError):
    pass
