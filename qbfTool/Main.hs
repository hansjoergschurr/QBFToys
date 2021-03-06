import Qdimacs 
import Thf
import SMTLib
import System.IO
import System.Environment
import Text.Printf
import System.Console.GetOpt
import System.Exit
import Data.ByteString.Lazy.Builder (hPutBuilder)

data Flag = Normalize | Invert | SMTLib |  Output String
    deriving (Eq,Ord,Show)


flags = [Option ['n'] [] (NoArg Normalize)
            "Outputs a standard complient Qdimacs problem.",
         Option ['s'] [] (NoArg SMTLib)
            "Output an SMT-LIB 2 problem.",
         Option ['i'] [] (NoArg Invert)
            (unlines ["Negates the generated THF problem. The conjecture is",
             "a theorem iff the QBF formular is false."]),
         Option ['o'] [] (ReqArg Output "FILE")
            "Output FILE"]

header = unlines ["Usage: convert [-n] [-s] [-i] [-o FILE]\n",
         "If an output filename is given a line containing the",
         "number of variables, clauses and if the problem was",
         "\"Trivally True\" (contained no clause) or \"Trivally False\"",
         "(contained the empty clause) is written to stdout."]

getOutfileName ∷ [Flag] → Maybe String
getOutfileName = foldl f Nothing 
    where f (Just a) _ = Just a
          f _ (Output s) = Just s
          f _ _ = Nothing
    
cleanQBF ∷ QBFProblem → (String, QBFProblem)
cleanQBF p = (s,p'')
    where 
        p' = (normalizeVars.quantifieUndeclaredVars) p
        (c, p'') = isTrivial p'
        (nv, nc) = qbfSizeNaive p''
        s = printf "%d %d %s" nv nc (case c of
                Nothing → ""
                Just True → "Trivally True"
                Just False → "Trivally False")

outputFun args
    | Normalize `elem` args  = toQdimacs
    | SMTLib `elem` args  = toSMTLib (Invert `elem` args)
    | otherwise = toThf (Invert `elem` args)

main ∷ IO ()
main = do
    args ← getArgs
    case getOpt Permute flags args of
        (args,_,[]) → do
            input ← getContents
            let prop = readProblem $ lines input 
                (desc, prop') = cleanQBF prop
                output = (outputFun args) prop'
                maybePath = getOutfileName args
            case maybePath of
                Just path → do 
                    handle ← openFile path WriteMode
                    hSetBinaryMode handle True
                    hSetBuffering handle $ BlockBuffering Nothing
                    hPutBuilder handle output
                    hClose handle
                    putStrLn desc
                Nothing → do 
                    -- stdout!
                    hPutBuilder stdout output
        (_,_,errs) → do
            hPutStrLn stderr (concat errs ++ usageInfo header flags)
            exitWith (ExitFailure 1)

