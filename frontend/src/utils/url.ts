export const fetchParameterByUrl = (url: string) => {
    const { searchParams } = new URL(url);
    const companyId = searchParams.get("company_id");
    const timestamp = searchParams.get("timestamp");
    const hmac = searchParams.get("hmac");

    return {
        hmac: hmac ?? "",
        timestamp: timestamp ?? "",
        companyId: companyId ?? "",
    };
};

export const fetchParameter = async (params: Record<string, string | string[] | undefined>) => {
    while (typeof window === "undefined") {
        await new Promise(resolve => setTimeout(resolve, 50));
    }

    const { hmac, timestamp, companyId } = fetchParameterByUrl(window.location.href);
    console.log('companyId', companyId);

    return new URLSearchParams({
        hmac: hmac ?? "",
        timestamp: timestamp ?? "",
        company_id: companyId ?? "",
    });
};
