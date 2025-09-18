import { useEffect, useState } from "react"

const useFetch = <T>(fetchFunction: () => Promise<T>, autoFetch = true) => {

    const [data, setData] = useState<T | null>(null);

    const [loading, setLoading] = useState(false);

    const [error, setError] = useState<Error|null>(null);




    const fetchData = async () => {
        try {
            setLoading(true)
            setError(null)

            const results = await fetchFunction();

            setData(results)

        } catch (err) {
            setError(err instanceof Error ? err : new Error("An error occurred!"));


        } finally {
            setLoading(false);
        }
    }

    const reset = () => {
        setLoading(false)
        setError(null)

        setData(null)
    }

    

    const execute = async ({params}: any) => {
        try {
            setLoading(true)
            setError(null)

            const results = await fetchFunction(params);

            setData(results)

        } catch (err) {
            setError(err instanceof Error ? err : new Error("An error occurred!"));


        } finally {
            setLoading(false);
        }
    }       


    useEffect(()=>{
        if(autoFetch){

            fetchData();
        }
    }, []);

    return {data, loading, error, refetch: fetchData, reset, execute}

}



export default useFetch