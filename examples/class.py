from xntricweb.xapi import XAPI, Entrypoint

xapi = XAPI()


class Math(Entrypoint):

    def sub(
        self,
        term: float,
        subtrahend: float,
        *subtrahends: float,
        precision: int = 2,
    ):
        """Performs subtraction operations.
        :param term:float The minuend to subtract from.
        :param subtrahend:float The subtrahend to subtract from the minuend.
        :param subtrahends:list[float] Additional subtrahends to subtract
            from the minuend.
        """
        print(round(term - subtrahend - (sum(subtrahends)), precision))
        return 0


xapi.entrypoint(Math())


@xapi.entrypoint
class DumbMath(Entrypoint):

    def sub(
        self,
        term: float,
        subtrahend: float,
        *subtrahends: float,
        precision: int = 2,
    ):
        """Performs subtraction operations.
        :param term:float The minuend to subtract from.
        :param subtrahend:float The subtrahend to subtract from the minuend.
        :param subtrahends:list[float] Additional subtrahends to subtract
            from the minuend.
        """
        print(round(term - subtrahend - (sum(subtrahends)), precision))
        return 0


xapi.run()
